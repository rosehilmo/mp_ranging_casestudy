#!/usr/bin/env python3
"""Estimate whale-to-station ranges from autocorrelation multipath timings.

Config-driven rewrite of plot_ranges_calltimings_autocorr_Brydes.py. For each
autocorrelation minute, the strongest multipath timing is matched against a
theoretical timing-vs-distance curve (BELLHOP ray table or the analytic ranging
model) to estimate range. Results are written to a CSV and plotted.

Example:
    whaletracks-plot-ranges --config whaletracks/config/plot_ranges.yaml \
        --station B01 --save ranges_B01.png
"""

import argparse
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.dates import DateFormatter

from whaletracks.cli._common import LOG, load_yaml, setup_logging
from whaletracks.detection import basic_ranging_model as ranging


def _load_ranging(cfg, station):
    """Return (distance, mp_1_timing, mp_2_timing, mp_3_timing, mp_1_sub).

    ``mp_1_sub`` is None unless a reflectivity table column is present.
    """
    source = cfg["ranging_source"]
    if source == "bellhop":
        path = os.path.join(cfg["bellhop_dir"], cfg["bellhop_template"].format(station=station))
        df = pd.read_csv(path)
        distance = df["interp_r"]
        t0, t1, t2, t3 = df["interp_d"], df["interp_mp1"], df["interp_mp2"], df["interp_mp3"]
        mp_1_timing = np.subtract(t1, t0)
        mp_2_timing = np.subtract(t2, t1)
        mp_3_timing = np.subtract(t3, t2)
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


def estimate_ranges(cfg, station, save=None, show=False):
    """Match multipath timings to ranges for one station; write CSV, plot."""
    distance, mp_1_timing, mp_2_timing, mp_3_timing, mp_1_sub = _load_ranging(cfg, station)
    reflectivity = bool(cfg.get("reflectivity"))

    calls_path = os.path.join(cfg["calls_dir"], cfg["calls_template"].format(station=station))
    auto_path = os.path.join(cfg["calls_dir"], cfg["auto_template"].format(station=station))

    df_calls = pd.read_csv(calls_path)
    df_calls["peak_time"] = pd.to_datetime(df_calls["peak_time"])
    calltimes = df_calls["peak_time"].unique()

    df1 = pd.read_csv(auto_path)
    dates = [pd.to_datetime(d) for d in df1["date"].tolist()]

    autotimes_save = []
    autopeaks_mp1_save = []
    autopeaks_mp2_save = []
    autopeaks_mp3_save = []
    auto_max = []
    auto_snr = []
    auto_amp = []
    auto_count = []
    center_calls = []
    low_freq_snr = []
    droprows = []

    t1_prev = 0
    for row in range(len(df1)):
        df = df1.iloc[row]
        t2 = df["arrival_2"] - df["arrival_1"]
        date = dates[row]
        start_center_min = date - pd.Timedelta(seconds=30)
        end_center_min = date + pd.Timedelta(seconds=30)
        unique_calls = calltimes[(calltimes > start_center_min) & (calltimes < end_center_min)]

        if len(unique_calls) > 0:
            mpdiff_1 = df["arrival_2"] - df["arrival_1"]
            mpdiff_2 = df["arrival_3"] - df["arrival_1"]
            mpdiff_3 = df["arrival_4"] - df["arrival_1"]
            mpdiff_4 = df["arrival_5"] - df["arrival_1"]

            timings = [mpdiff_1, mpdiff_2, mpdiff_3, mpdiff_4]
            amps = [df["amp_2"], df["amp_3"], df["amp_4"], df["amp_5"]]
            max_ind = amps.index(max(amps))
            mp_timing = timings[max_ind]

            near_timings = [abs(mp - mp_timing) for mp in mp_1_timing]
            near_timings_2 = [abs(mp - mp_timing) for mp in mp_2_timing]
            near_timings_3 = [abs(mp - mp_timing) for mp in mp_3_timing]

            match_ind = near_timings.index(min(near_timings))
            match_ind_2 = near_timings_2.index(min(near_timings_2))
            match_ind_3 = near_timings_3.index(min(near_timings_3))

            best_distance = distance[match_ind]
            best_distance_2 = distance[match_ind_2]
            best_distance_3 = distance[match_ind_3]

            if best_distance < 110 and reflectivity and mp_1_sub is not None:
                near_timings_sub = [abs(mp - mp_timing) for mp in mp_1_sub]
                match_ind_sub = near_timings_sub.index(min(near_timings_sub))
                best_distance_sub = distance[match_ind_sub]
                plt.scatter(date, best_distance_sub / 1000, c="pink", zorder=1)
                best_distance = best_distance_sub
                autopeaks_mp1_save += [best_distance_sub / 1000]
            else:
                autopeaks_mp1_save += [best_distance / 1000]

            autotimes_save += [date]
            auto_max += [df["peaks"]]
            auto_snr += [df["snr"]]
            auto_amp += [df["db_amps"]]
            auto_count += [df["sum_calls"]]
            center_calls += [df["n_calls"]]
            low_freq_snr += [df["low_snr"]]
            autopeaks_mp2_save += [best_distance_2 / 1000]
            autopeaks_mp3_save += [best_distance_3 / 1000]

        if t1_prev == t2:
            droprows += [row]
        t1_prev = t2

    df1.drop(index=droprows, inplace=True)
    saveranges = pd.DataFrame(
        {
            "time": autotimes_save,
            "range_D_MP1": autopeaks_mp1_save,
            "range_MP1_MP2": autopeaks_mp2_save,
            "range_MP2_MP3": autopeaks_mp3_save,
            "auto_max": auto_max,
            "auto_snr": auto_snr,
            "auto_amp": auto_amp,
            "auto_count": auto_count,
            "n_calls": center_calls,
        }
    )

    # Quality filter for the scatter plot
    enough_samps = np.where(np.array(auto_max) > cfg["filters"]["min_auto_max"])
    no_low_noise = np.where(np.array(low_freq_snr) < cfg["filters"]["max_low_freq_snr"])
    suminds = np.intersect1d(enough_samps, no_low_noise)

    timesarray = np.array(autotimes_save)
    peaksarray1 = np.array(autopeaks_mp1_save)
    peaksarray2 = np.array(autopeaks_mp2_save)
    peaksarray3 = np.array(autopeaks_mp3_save)
    colarray = np.array(auto_amp)

    fig, ax = plt.subplots(figsize=(13, 6))
    plt.scatter(timesarray[suminds], peaksarray1[suminds], c=colarray[suminds], cmap="gist_ncar")
    plt.scatter(timesarray[suminds], peaksarray2[suminds], c=colarray[suminds],
                marker="x", cmap="gist_ncar")
    plt.scatter(timesarray[suminds], peaksarray3[suminds], c=colarray[suminds],
                marker="+", cmap="gist_ncar")
    plt.grid(axis="both")
    plt.title("Ranges for mp1/mp2/mp3 timings; colour = dB amplitude of strongest arrival")
    plt.xlabel("Time", fontsize=16)
    plt.ylabel("Distance (km)", fontsize=16)
    plt.ylim(*cfg["ylim_km"])
    plt.colorbar()
    ax.xaxis.set_major_formatter(DateFormatter("%m/%d %H%M"))

    out_path = os.path.join(cfg["output_dir"], cfg["output_template"].format(station=station))
    os.makedirs(cfg["output_dir"], exist_ok=True)
    saveranges.to_csv(out_path, index=False)
    LOG.info("Wrote %s (%d range rows, %d passed filter)", out_path, len(saveranges), len(suminds))

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
    estimate_ranges(cfg, args.station, save=args.save, show=args.show)


if __name__ == "__main__":
    main()
