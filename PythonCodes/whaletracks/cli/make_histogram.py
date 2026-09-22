#!/usr/bin/env python3
"""Plot a histogram of Bryde's-whale detections over a deployment year.

Config-driven rewrite of make_year_histogram_Brydes_calls.py. Reads a
detection CSV, keeps calls at or above a detection-score threshold, and plots
a histogram of their peak times. Use the plot's zoom tools to inspect
specific days, or pass --save to write a figure instead of showing it.

Example:
    whaletracks-histogram --input B12_mp_Brydes_Year_LongCall.csv --threshold 5000
"""

import argparse

import matplotlib.pyplot as plt
import pandas as pd

from whaletracks.cli._common import LOG, setup_logging


def make_histogram(input_path, threshold=5000, bins=350, save=None):
    """Plot (or save) a histogram of detection peak-times above ``threshold``."""
    df = pd.read_csv(input_path)
    df["peak_time"] = pd.to_datetime(df["peak_time"])
    strong = df.loc[df["peak_signal"] >= threshold]
    LOG.info("%d of %d detections at or above threshold %s", len(strong), len(df), threshold)

    plt.hist(strong.peak_time, bins=bins)
    plt.xlabel("Date")
    plt.ylabel("Count")
    if save:
        plt.savefig(save, dpi=300, bbox_inches="tight")
        LOG.info("Wrote %s", save)
    else:
        plt.show()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Detection CSV path")
    parser.add_argument("--threshold", type=float, default=5000,
                        help="Minimum peak_signal to include (default: 5000)")
    parser.add_argument("--bins", type=int, default=350, help="Histogram bins (default: 350)")
    parser.add_argument("--save", help="Write figure to this path instead of showing it")
    parser.add_argument("--verbose", action="store_true", help="Debug logging")
    args = parser.parse_args(argv)

    setup_logging(args.verbose)
    make_histogram(args.input, threshold=args.threshold, bins=args.bins, save=args.save)


if __name__ == "__main__":
    main()
