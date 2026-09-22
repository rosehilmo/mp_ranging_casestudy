#!/usr/bin/env python3
"""Interactively pick Bryde's whale calls from spectrograms.

Config-driven rewrite of the former Brydes_manual_picker.py script. Downloads
data, makes a spectrogram, and asks the user (via matplotlib ``ginput``) to
click on observed calls; computes SNR and frequency features for each pick and
writes them to a CSV.

Requires IRIS network access and an interactive matplotlib backend.

Example:
    whaletracks-pick --config whaletracks/config/manual_picker.yaml
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
from whaletracks.detection import manual_picking as detect

# Output dataframe structure (do not reorder: downstream tooling relies on it)
DF_COLUMNS = [
    "start_time",
    "start_epoch",
    "start_frequency",
    "snr",
    "call_type",
    "ambient_snr",
    "station",
    "channel",
    "peak_frequency",
    "peak_frequency_std",
]


def run_picker(cfg, config_path):
    """Run the interactive picking loop over the configured time window."""
    chunk_length = cfg["chunk_length_s"]
    chunk_file = resolve_relative(config_path, cfg["chunk_file"])
    detection_path = resolve_relative(config_path, cfg["detection_file"])
    is_restart = bool(cfg.get("is_restart", False))
    station_list = cfg["station_list"]
    channel = cfg["channel"]
    freqlim = cfg["spectrogram"]["freqlim"]

    utcstart = UTCDateTime(cfg["starttime"])
    utcend = UTCDateTime(cfg["endtime"])
    utcstart_chunk = utcstart
    utcend_chunk = utcstart + chunk_length

    client = Client(cfg["client"])

    brydes_calls = pd.DataFrame(columns=DF_COLUMNS)
    while utcend > utcstart_chunk:
        # Either load working pick file or make a new one
        if os.path.isfile(chunk_file) and is_restart:
            brydes_calls = pd.read_csv(chunk_file)
        else:
            brydes_calls = pd.DataFrame(columns=DF_COLUMNS)

        LOG.info("Start time %s", utcstart_chunk)

        for station_ids in station_list:
            st_raw = None
            retry = 0

            # Get waveform from IRIS
            while st_raw is None and retry < cfg["max_retries"]:
                try:
                    st_raw = client.get_waveforms(
                        network=cfg["network"],
                        station=station_ids,
                        location=cfg["location"],
                        channel=channel,
                        starttime=utcstart_chunk,
                        endtime=utcend_chunk,
                        attach_response=True,
                    )
                except Exception:
                    retry += 1
                    st_raw = None
                    LOG.warning("Client failed: retry %d of %d", retry, cfg["max_retries"])

            # If data does not exist, move on to next time chunk
            if st_raw is None:
                LOG.warning("No data available from input station/times")
                utcstart_chunk = utcstart_chunk + chunk_length
                utcend_chunk = utcend_chunk + chunk_length
                continue

            # Filter waveform, remove response and sensitivity
            st_raw.detrend(type="demean")
            st_raw.detrend(type="linear")
            st_raw.remove_response(output="VEL", pre_filt=cfg["response"]["pre_filt"])
            st_raw.remove_sensitivity()

            tr_filt = st_raw[0].copy()

            # Make spectrogram of data
            [f, t, Sxx] = detect.plotwav(
                tr_filt.stats.sampling_rate,
                tr_filt.data,
                window_size=cfg["spectrogram"]["window_size"],
                overlap=cfg["spectrogram"]["overlap"],
                plotflag=False,
            )

            # Subsample spectrogram to call range and convert to dB
            freq_inds = np.where(np.logical_and(f >= min(freqlim), f <= max(freqlim)))
            f_sub = f[freq_inds]
            Sxx_sub = Sxx[freq_inds, :][0]
            Sxx_log1 = 10 * np.log10(Sxx_sub)
            Sxx_log = Sxx_log1 - np.min(Sxx_log1)

            # Choose color range for spectrogram
            vmin = np.median(Sxx_log) + 2 * np.std(Sxx_log)
            vmax = np.median(Sxx_log)

            t1 = min(t)
            t2 = max(t)
            fig = plt.figure(figsize=tuple(cfg["plot"]["figsize"]))
            ax1 = fig.add_subplot(111)

            cmap = plt.get_cmap("viridis")
            norm = color.Normalize(vmin=vmin, vmax=vmax)
            im = ax1.pcolormesh(t, f_sub, Sxx_log, cmap=cmap, norm=norm)
            fig.colorbar(im, ax=ax1, orientation="horizontal")
            ax1.set_xlim([t1, t2])
            ax1.set_ylim(cfg["plot"]["ylim"])
            ax1.set_ylabel("Frequency [Hz]")
            ax1.set_xlabel(
                "Seconds past " + UTCDateTime.strftime(utcstart_chunk, "%Y-%m-%dT%H:%M:%S.%fZ")
            )
            ax1.set_title("Select calls")
            fig.tight_layout()

            # Request user input to select calls
            LOG.info("Select all Brydes calls at starting time and frequency")
            bry_calls = plt.ginput(n=-1, timeout=-1)

            # Format Brydes calls
            b_picks = []
            b_freq = []
            for inds in range(0, len(bry_calls)):
                ind = inds - 1
                b_picks = b_picks + [utcstart_chunk + bry_calls[ind][0]]
                b_freq = b_freq + [bry_calls[ind][1]]
            b_epochs = detect.datetime_to_epoch(b_picks)
            btype = list(np.repeat("B", len(b_epochs)))

            all_picks = b_picks
            all_epochs = b_epochs
            all_freq = b_freq
            all_type = btype

            # SNR analysis of manual detections
            snr_cfg = cfg["snr"]
            [snr, ambient_snr] = detect.get_snr(
                all_picks,
                t,
                f_sub,
                Sxx_sub,
                utcstart_chunk,
                snr_limits=snr_cfg["limits"],
                snr_calllength=snr_cfg["calllength"],
                snr_freqwidth=snr_cfg["freqwidth"],
                dur=snr_cfg["dur"],
            )
            # Frequency analysis of manual detections
            [peak_freq, freq_std] = detect.freq_analysis(
                all_picks, all_type, t, f_sub, Sxx_sub, utcstart_chunk
            )

            # Build detections dictionary
            dct = {k: [] for k in DF_COLUMNS}
            for index in range(0, len(all_picks)):
                dct["start_time"].append(all_picks[index])
                dct["start_epoch"].append(all_epochs[index])
                dct["start_frequency"].append(all_freq[index])
                dct["call_type"].append(all_type[index])
                dct["station"].append(station_ids)
                dct["channel"].append(channel)
                dct["snr"].append(snr[index])
                dct["ambient_snr"].append(ambient_snr[index])
                dct["peak_frequency"].append(peak_freq[index])
                dct["peak_frequency_std"].append(freq_std[index])

            brydes_calls_sta = pd.DataFrame(dct)

            frames = [
                df
                for df in [brydes_calls, brydes_calls_sta]
                if not df.empty and not df.isna().all().all()
            ]
            brydes_calls = pd.concat(frames)
            brydes_calls.to_csv(chunk_file, index=False)

            plt.close()

        utcstart_chunk = utcstart_chunk + chunk_length
        utcend_chunk = utcend_chunk + chunk_length

    if len(brydes_calls) == 0:
        LOG.warning("Detections dataframe empty")
    else:
        brydes_calls.to_csv(detection_path, index=False)
        LOG.info("Wrote %s", detection_path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--verbose", action="store_true", help="Debug logging")
    args = parser.parse_args(argv)

    setup_logging(args.verbose)
    cfg = load_yaml(args.config)
    run_picker(cfg, args.config)


if __name__ == "__main__":
    main()
