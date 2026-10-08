#!/usr/bin/env python3
"""Estimate whale-to-station ranges from autocorrelation multipath timings.

Config-driven. For each autocorrelation minute, the strongest multipath timing
is matched against a theoretical timing-vs-distance curve (BELLHOP ray table or
the analytic ranging model) to estimate range. Results are written to a CSV
(with a provenance sidecar) and plotted.

Example:
    whaletracks-plot-ranges --config whaletracks/config/ranges_fin.yaml \
        --station B20 --save ranges_B20.png
"""

import argparse
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.dates import DateFormatter

from whaletracks.cli._common import LOG, load_yaml, setup_logging
from whaletracks.common import provenance
from whaletracks.detection import basic_ranging_model as ranging
from whaletracks.detection.range_estimation import (
    bellhop_timings,
    estimate_ranges_from_timings,
)


def _load_ranging(cfg, station):
    """Return (distance, mp_1_timing, mp_2_timing, mp_3_timing, mp_1_sub).

    ``mp_1_sub`` is None unless a reflectivity table column is present.
    """
    source = cfg["ranging_source"]
    if source == "bellhop":
        path = os.path.join(cfg["bellhop_dir"], cfg["bellhop_template"].format(station=station))
        df = pd.read_csv(path)
        distance, mp_1_timing, mp_2_timing, mp_3_timing = bellhop_timings(df)
        mp_1_sub = df["interp_sub"] if (cfg.get("reflectivity") and "interp_sub" in df) else None
        return distance, mp_1_timing, mp_2_timing, mp_3_timing, mp_1_sub

    if source == "analytic":
        a = cfg["analytic"]
        distance, t0, t1, t2, t3, _, _, _ = ranging.basic_ranging(
            a["depth"], a["ss"], a["sed_speed"], a["t"], plotflag=False
        )
        mp_1_timing = np.subtract(t1, t0)
        mp_2_timing = np.subtract(t2, t1)
        # NOTE: the legacy analytic branch never defined mp_3_timing, so its
        # range loop raised NameError. We fill it as t3-t2 (consistent with the
        # bellhop branch). See KNOWN_ISSUES.md.
        LOG.warning(
            "analytic ranging: filling mp_3_timing = t3 - t2 (undefined in the legacy script)"
        )
        mp_3_timing = np.subtract(t3, t2)
        return distance, mp_1_timing, mp_2_timing, mp_3_timing, None

    raise ValueError(f"Unknown ranging_source: {source!r} (expected 'bellhop' or 'analytic')")


def _unique(df, column):
    """The single value of ``column``, or None if absent/mixed."""
    if column not in df:
        return None
    values = df[column].dropna().unique()
    return str(values[0]) if len(values) == 1 else None


def _bellhop_path(cfg, station):
    """Path of the station's BELLHOP table, or None in analytic mode."""
    if cfg["ranging_source"] != "bellhop":
        return None
    return os.path.join(cfg["bellhop_dir"], cfg["bellhop_template"].format(station=station))


def estimate_ranges(cfg, station, save=None, show=False, config_path=None):
    """Match multipath timings to ranges for one station; write CSV, plot.

    Also writes a provenance sidecar next to the CSV (see
    ``whaletracks.common.provenance``).
    """
    distance, mp_1_timing, mp_2_timing, mp_3_timing, mp_1_sub = _load_ranging(cfg, station)

    calls_path = os.path.join(cfg["calls_dir"], cfg["calls_template"].format(station=station))
    auto_path = os.path.join(cfg["calls_dir"], cfg["auto_template"].format(station=station))

    df_calls = pd.read_csv(calls_path)
    df_calls["peak_time"] = pd.to_datetime(df_calls["peak_time"])
    df_auto = pd.read_csv(auto_path)

    gate = cfg.get("ranging", {})
    saveranges = estimate_ranges_from_timings(
        df_auto, df_calls["peak_time"].unique(),
        distance, mp_1_timing, mp_2_timing, mp_3_timing,
        reflectivity=bool(cfg.get("reflectivity")), mp_1_sub=mp_1_sub,
        valid_start=cfg.get("valid_start"), valid_end=cfg.get("valid_end"),
        min_center=gate.get("min_center", 1),
        min_window=gate.get("min_window", 0),
        window_length_s=gate.get("window_length_s", 1200),
    )

    out_path = os.path.join(cfg["output_dir"], cfg["output_template"].format(station=station))
    os.makedirs(cfg["output_dir"], exist_ok=True)
    saveranges.to_csv(out_path, index=False)

    # Network and station come from the detection CSV itself rather than the
    # config, so they describe the data that was actually ranged. The waveform
    # channel is recorded by the detection step (see its manifest).
    inputs = [calls_path, auto_path]
    bellhop_path = _bellhop_path(cfg, station)
    if bellhop_path:
        inputs.append(bellhop_path)
    provenance.write_manifest(
        out_path,
        command="whaletracks-plot-ranges",
        config_path=config_path,
        parameters={
            "ranging_source": cfg["ranging_source"],
            "reflectivity": bool(cfg.get("reflectivity")),
            "valid_start": cfg.get("valid_start"),
            "valid_end": cfg.get("valid_end"),
            "ranging": {
                "min_center": gate.get("min_center", 1),
                "min_window": gate.get("min_window", 0),
                "window_length_s": gate.get("window_length_s", 1200),
            },
        },
        source={
            "network": _unique(df_calls, "network_code"),
            "station": _unique(df_calls, "station_code") or station,
            "time_span": provenance.time_span(saveranges["time"]),
        },
        inputs=inputs,
        rows=len(saveranges),
    )

    # The CSV keeps every ranged window; the scatter plot shows those above the
    # auto_max quality threshold, coloured by the dB amplitude of the strongest
    # arrival.
    keep = saveranges[saveranges["auto_max"] > cfg["filters"]["min_auto_max"]]
    fig, ax = plt.subplots(figsize=(13, 6))
    for marker, col in (("o", "range_D_MP1"), ("x", "range_MP1_MP2"), ("+", "range_MP2_MP3")):
        plt.scatter(keep["time"], keep[col], c=keep["auto_amp"], marker=marker, cmap="gist_ncar")
    plt.grid(axis="both")
    plt.title("Ranges for mp1/mp2/mp3 timings; colour = dB amplitude of strongest arrival")
    plt.xlabel("Time", fontsize=16)
    plt.ylabel("Distance (km)", fontsize=16)
    plt.ylim(*cfg["ylim_km"])
    plt.colorbar()
    ax.xaxis.set_major_formatter(DateFormatter("%m/%d %H%M"))

    LOG.info("Wrote %s (%d range rows, %d passed filter)", out_path, len(saveranges), len(keep))
    if save:
        fig.savefig(save, dpi=300, bbox_inches="tight")
        LOG.info("Wrote %s", save)
    if show:
        plt.show()
    plt.close(fig)
    return saveranges


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--station", required=True, help="Station code, e.g. B01")
    parser.add_argument("--save", help="Write the scatter figure to this path")
    parser.add_argument("--show", action="store_true", help="Display the figure interactively")
    parser.add_argument("--verbose", action="store_true", help="Debug logging")
    args = parser.parse_args(argv)

    setup_logging(args.verbose)
    cfg = load_yaml(args.config)
    estimate_ranges(cfg, args.station, save=args.save, show=args.show,
                    config_path=args.config)


if __name__ == "__main__":
    main()
