#!/usr/bin/env python3
"""Semi-automated multipath hypothesis selection (CLI).

Config-driven. Runs the automated part — filter, group, qualify, link
supertracks, assign best hypotheses — and writes
``{station}_grouped_ranges.csv``. With ``--review`` it then runs the interactive
analyst verification (requires a display): each group is shown in context and
the analyst accepts (0), overrides the hypothesis (1/2/3) or rejects the group
(9); the corrected table is written alongside as ``*_corrected.csv``.

Example:
    whaletracks-select --config whaletracks/config/select_fin.yaml --station B20
"""

import argparse
import os

import pandas as pd

from whaletracks.cli._common import LOG, load_yaml, setup_logging
from whaletracks.detection.hypothesis_selection import (
    select_hypotheses,
    selected_range,
)


def run_selection(cfg, station):
    """Automated selection for one station; returns the grouped table."""
    path = os.path.join(cfg["input_dir"], cfg["input_template"].format(station=station))
    ranges_df = pd.read_csv(path)

    flt, grp = cfg["filter"], cfg["grouping"]
    qual, sup = cfg["qualify"], cfg["supertrack"]
    grouped = select_hypotheses(
        ranges_df,
        start=flt.get("start"),
        max_range_km=flt["max_range_km"],
        min_window_calls=flt["min_window_calls"],
        saturation_km=flt["saturation_km"],
        range_jump_km=grp["range_jump_km"],
        time_gap=pd.Timedelta(hours=grp["time_gap_hours"]),
        min_group_rows=qual["min_group_rows"],
        min_mean_calls=qual["min_mean_calls"],
        supertrack_gap=pd.Timedelta(hours=sup["gap_hours"]),
        max_segment_groups=sup["max_segment_groups"],
    )

    n_tracks = grouped["use_track"].sum()
    n_super = grouped["supertrack"].nunique(dropna=True)
    LOG.info(
        "%s: %d rows in, %d rows in qualifying groups, %d supertracks",
        station, len(grouped), n_tracks, n_super,
    )
    return grouped


def review_groups(grouped):
    """Interactive analyst verification loop (requires a display).

    Mutates ``grouped``: 0 accepts, 1/2/3 overrides the hypothesis for the
    group, 9 rejects the group (use_track False, supertrack/hypothesis NaN).
    """
    import matplotlib.pyplot as plt

    tracks = grouped[grouped["use_track"] == True]  # noqa: E712
    for st in sorted(tracks["supertrack"].dropna().unique()):
        sub = grouped[grouped["supertrack"] == st]
        for gid in sub["groupnum"].dropna().unique():
            fig, ax = plt.subplots(figsize=(12, 5))
            for col, colour, marker in (
                ("range_D_MP1", "0.5", "o"),
                ("range_MP1_MP2", "0.7", "p"),
                ("range_MP2_MP3", "0.8", "+"),
            ):
                ax.scatter(sub["time"], sub[col], c=colour, marker=marker, s=30)
            g = grouped[grouped["groupnum"] == gid]
            ax.scatter(g["time"], selected_range(g), c="tab:red", s=60,
                       label=f"group {gid:g} (selected)")
            ax.set_ylim(0, 40)
            ax.set_xlabel("Time")
            ax.set_ylabel("Range (km)")
            ax.legend()
            plt.show()

            x = input(
                "Correct hypothesis? 0 yes / 1 D-MP1 / 2 MP1-MP2 / 3 MP2-MP3 / 9 reject: "
            ).strip()
            rows = grouped["groupnum"] == gid
            if x == "9":
                grouped.loc[rows, "best_hypothesis"] = float("nan")
                grouped.loc[rows, "use_track"] = False
                grouped.loc[rows, "supertrack"] = float("nan")
            elif x in {"1", "2", "3"}:
                grouped.loc[rows, "best_hypothesis"] = int(x)
    return grouped


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--station", required=True, help="Station code, e.g. B20")
    parser.add_argument("--review", action="store_true",
                        help="Interactive analyst verification (needs a display)")
    parser.add_argument("--verbose", action="store_true", help="Debug logging")
    args = parser.parse_args(argv)

    setup_logging(args.verbose)
    cfg = load_yaml(args.config)
    grouped = run_selection(cfg, args.station)

    os.makedirs(cfg["output_dir"], exist_ok=True)
    out = os.path.join(
        cfg["output_dir"], cfg["output_template"].format(station=args.station)
    )
    grouped.to_csv(out, index=False)
    LOG.info("Wrote %s", out)

    if args.review:
        corrected = review_groups(grouped)
        out_corr = out.replace(".csv", "_corrected.csv")
        corrected.to_csv(out_corr, index=False)
        LOG.info("Wrote %s", out_corr)


if __name__ == "__main__":
    main()
