#!/usr/bin/env python3
"""Interactively verify detected Bryde's whale calls.

Config-driven rewrite of the former brydes_call_verification.py script. Makes a
spectrogram, overlays the detection times/scores from a detection CSV, and asks
the user (via matplotlib ``ginput``) to mark true / missed calls, writing a
``quality``-labelled CSV.

Requires IRIS network access and an interactive matplotlib backend.

Example:
    whaletracks-verify --config whaletracks/config/verify_calls.yaml
"""

import argparse
import os

import matplotlib.colors as color
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from obspy import UTCDateTime
from obspy.clients.fdsn import Client

from whaletracks.cli._common import LOG, load_yaml, resolve_relative, setup_logging
from whaletracks.common.util import datestr_to_epoch
from whaletracks.detection.detect_calls import plotwav


def run_verification(cfg, config_path):
    """Run the interactive verification loop for all configured stations."""
    chunk_length = cfg["chunk_length_s"]
    detection_file = resolve_relative(config_path, cfg["detection_file"])
    chunk_file = resolve_relative(config_path, cfg["chunk_file"])
    is_restart = bool(cfg.get("is_restart", False))
    station_list = cfg["station_list"]
    starttime = cfg["starttime"]
    freqlim = cfg["spectrogram"]["freqlim"]

    start_epoch = datestr_to_epoch([starttime], dateformat="%Y-%m-%dT%H:%M:%S.%f")
    end_epoch = [start_epoch[0] + chunk_length]

    utcstart_chunk = UTCDateTime(starttime)
    utcend_chunk = UTCDateTime(starttime) + chunk_length

    client = Client(cfg["client"])
    b_df = pd.read_csv(detection_file)

    # Either load working verification file or make a new one
    if os.path.isfile(chunk_file) and is_restart:
        verified_calls = pd.read_csv(chunk_file)
    else:
        verified_calls = pd.DataFrame(columns=b_df.columns)
        verified_calls["quality"] = []

    for station_ids in station_list:
        st_raw = None
        retry = 0
        chunk_verified = pd.DataFrame(columns=b_df.columns)

        # Filter detections for this station and date range
        b_df_sub = b_df.loc[
            (b_df["station_code"] == station_ids)
            & (b_df["peak_epoch"] > start_epoch[0])
            & (b_df["peak_epoch"] < end_epoch[0])
        ]

        # Get waveform from IRIS
        while st_raw is None and retry < cfg["max_retries"]:
            try:
                st_raw = client.get_waveforms(
                    network=cfg["network"],
                    station=station_ids,
                    location=cfg["location"],
                    channel=cfg["channel"],
                    starttime=utcstart_chunk,
                    endtime=utcend_chunk,
                    attach_response=True,
                )
            except Exception:
                retry += 1
                st_raw = None
                LOG.warning("Client failed: retry %d of %d", retry, cfg["max_retries"])

        if st_raw is None:
            LOG.warning("No data available from input station/times")
            continue

        # Filter waveform, remove response and sensitivity
        st_raw.detrend(type="demean")
        st_raw.detrend(type="linear")
        st_raw.remove_response(output="VEL", pre_filt=cfg["response"]["pre_filt"])
        st_raw.remove_sensitivity()

        tr_filt = st_raw[0].copy()

        # Make spectrogram of data
        [f, t, Sxx] = plotwav(
            tr_filt.stats.sampling_rate,
            tr_filt.data,
            filt_freqlim=cfg["spectrogram"]["filt_freqlim"],
            window_size=cfg["spectrogram"]["window_size"],
            overlap=cfg["spectrogram"]["overlap"],
            plotflag=False,
        )
        t = t + start_epoch

        # Subsample spectrogram to call range and convert to dB
        freq_inds = np.where(np.logical_and(f >= min(freqlim), f <= max(freqlim)))
        f_sub = f[freq_inds]
        Sxx_sub = Sxx[freq_inds, :][0]
        Sxx_log1 = 10 * np.log10(Sxx_sub)
        Sxx_log = Sxx_log1 - np.min(Sxx_log1)

        # Choose color range for spectrogram
        vmin = np.median(Sxx_log) + 1.5 * np.std(Sxx_log)
        vmax = np.median(Sxx_log)

        # Prepare call data for plotting
        b_start = b_df_sub["start_epoch"].values.tolist()
        b_end = b_df_sub["end_epoch"].values.tolist()
        b_score = b_df_sub["peak_signal"].values.tolist()
        b_peak = b_df_sub["peak_epoch"].values.tolist()

        t1 = min(t)
        t2 = max(t)
        fig, (ax0, ax1) = plt.subplots(nrows=2, sharex=True)
        fig.set_figheight(6)
        fig.set_figwidth(15)

        # plot calls on upper axis
        for b_ind in range(0, len(b_start)):
            ax0.plot([b_start[b_ind], b_end[b_ind]], [b_score[b_ind], b_score[b_ind]], "m")
            ax0.plot(b_peak, b_score, "mx")

        ax0.set_xlim([t1, t2])
        ax0.set_ylim([0, np.max(b_score + [1]) + 0.2])
        ax0.set_xlabel("Seconds")
        ax0.set_ylabel("Detection score")
        ax0.set_title("Detection score, peak time, and width")

        # plot spectrogram on lower axis
        cmap = plt.get_cmap("viridis")
        norm = color.Normalize(vmin=vmin, vmax=vmax)
        im = ax1.pcolormesh(t, f_sub, Sxx_log, cmap=cmap, norm=norm)
        fig.colorbar(im, ax=ax1, orientation="horizontal")
        for b_ind in range(0, len(b_start)):
            ax1.plot([b_peak[b_ind], b_peak[b_ind]], [10, 50], "m-")
        ax1.set_xlim([t1, t2])
        ax1.set_ylim(cfg["plot"]["ylim"])
        ax1.set_ylabel("Frequency [Hz]")
        fig.tight_layout()

        # Request user input to select calls
        LOG.info("Select detected calls that are true")
        true_calls = plt.ginput(n=-1, timeout=-1)
        LOG.info("Select missed calls that are true")
        missed_calls = plt.ginput(n=-1, timeout=-1)

        quality_list = []
        for inds in range(0, len(true_calls)):
            ind = inds - 1
            diff_list = abs(np.subtract(b_peak, true_calls[ind][0]))
            diff = min(diff_list)
            if diff < 10:
                k = np.argmin(diff_list)
                chunk_verified = pd.concat(
                    [chunk_verified, b_df_sub.iloc[k].to_frame().T], axis=0, ignore_index=True
                )
                quality_list = quality_list + [1]

        df_false = pd.concat([b_df_sub, chunk_verified]).drop_duplicates(keep=False)
        quality_list = quality_list + [0] * len(df_false)

        chunk_verified = pd.concat([chunk_verified, df_false])
        chunk_verified["quality"] = quality_list

        for inds2 in range(0, len(missed_calls)):
            ind2 = inds2 - 1
            new_row = [None] * len(chunk_verified.columns)
            new_row[-1] = 1
            new_row[-3] = station_ids
            new_row[5] = missed_calls[ind2][0]
            df_len = len(chunk_verified)
            chunk_verified.loc[df_len] = new_row

        verified_calls = pd.concat([verified_calls, chunk_verified])
        plt.close()

    verified_calls.to_csv(chunk_file, index=False)
    LOG.info("Wrote %s", chunk_file)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--verbose", action="store_true", help="Debug logging")
    args = parser.parse_args(argv)

    setup_logging(args.verbose)
    cfg = load_yaml(args.config)
    run_verification(cfg, args.config)


if __name__ == "__main__":
    main()
