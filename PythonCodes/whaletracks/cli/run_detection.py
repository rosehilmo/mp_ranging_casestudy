#!/usr/bin/env python3
"""Detect Bryde's whale calls and estimate multipath ranges.

Config-driven rewrite of the former MP_Marianas_automation_Brydes.py script.
Per-station geometry, channel, and date ranges are read from a station-info
CSV; all other parameters come from a per-species YAML config (see
config/detect_brydes.yaml and config/detect_fin.yaml).

Example:
    whaletracks-detect --config whaletracks/config/detect_fin.yaml
    whaletracks-detect --config whaletracks/config/detect_brydes.yaml --station B19
"""

import argparse
import math
import os

import numpy as np
import pandas as pd
import scipy.signal as sig
from obspy import UTCDateTime
from obspy.clients.fdsn import Client
from scipy.interpolate import interp1d
from scipy.signal import hilbert

from whaletracks.cli._common import LOG, load_yaml, setup_logging
from whaletracks.common import constants as cn
from whaletracks.common.util import datetime_to_epoch
from whaletracks.detection import basic_ranging_model as ranging
from whaletracks.detection import detect_calls as detect
from whaletracks.detection.event_analyzer import EventAnalyzer


def run_station(
    client,
    network,
    station,
    location,
    channel,
    starttime,
    endtime,
    kernel,
    spectrogram,
    snr,
    event,
    multipath,
    ranging_thresholds,
    amps,
    sound_speed,
    response,
    day_length,
    chunk_length,
    dt_up,
    dt_down,
    max_retries,
    chunk_path,
    auto_path,
    detection_path,
    is_restart,
    plotflag=False,
):
    """Run the detection + multipath pipeline for a single station.

    All parameters are explicit and supplied from a species config (Bryde's or
    fin). Species differences — kernel, frequency bands, SNR/EQ bands, event
    thresholds, autocorrelation window, ranging call-count thresholds, and the
    amplitude-envelope window — are all config-driven. ``snr['eq_band']`` is
    optional: when omitted (fin), the earthquake-band SNR column is not
    computed.
    """
    has_eq = bool(snr.get("eq_band"))
    if os.path.isfile(chunk_path) and is_restart:
        analyzers = [pd.read_csv(chunk_path)]
        auto_df_full = [pd.read_csv(auto_path)]
    else:
        analyzers = []
        auto_df_full = []

    utcstart = UTCDateTime(starttime)
    utcend = UTCDateTime(endtime)

    utcstart_chunk = utcstart
    utcend_chunk = utcstart + day_length

    analyzer_j = None
    while utcend > utcstart_chunk:
        LOG.info("Processing %s chunk starting %s", station, utcstart_chunk)

        retry = 0
        st_raw = None
        while st_raw is None and retry < max_retries:
            try:
                st_raw = client.get_waveforms(
                    network=network,
                    station=station,
                    location=location,
                    channel=channel,
                    starttime=utcstart_chunk - 0.5 * chunk_length,
                    endtime=utcend_chunk + 0.5 * chunk_length,
                    attach_response=True,
                )
            except Exception:
                retry += 1
                st_raw = None
                LOG.warning("Client failed: retry %d of %d", retry, max_retries)

        if st_raw is None:
            LOG.warning("No data available from input station/times")
            utcstart_chunk = utcstart_chunk + day_length
            utcend_chunk = utcend_chunk + day_length
            continue

        try:
            st_raw.detrend(type=response.get("detrend", "demean"))
            st_raw.remove_response(output=response["output"], pre_filt=response["pre_filt"])
        except Exception:
            # Occasional internet hiccups drop the connection; wait and retry
            # this chunk rather than skipping a large span of dates.
            LOG.warning("Connection reset error, retrying after pause")
            import time

            time.sleep(60 * 5)
            continue

        num_sta = len(st_raw)
        analyzers_chunk = []
        for idx in range(1, num_sta + 1):
            j = idx - 1
            tr_filt = st_raw[j].copy()
            samp = tr_filt.stats.sampling_rate
            # skip if less than ~1 min of data, or data is constant (bad)
            if len(tr_filt.data) < samp * 59:
                continue
            if tr_filt.data[0] == tr_filt.data[1]:
                continue

            freqlim = spectrogram["freqlim"]
            snr_limits = snr["limits"]

            # Spectrogram of the whole timeseries
            f, t, Sxx = detect.plotwav(
                samp,
                tr_filt.data,
                window_size=spectrogram["window_size"],
                overlap=spectrogram["overlap"],
                plotflag=False,
                filt_freqlim=freqlim,
                ylim=freqlim,
            )

            # Detection kernel matching the spectrogram grid
            tvec, fvec, blue_kernel, freq_inds = detect.buildkernel(
                kernel["f0"], kernel["f1"], kernel["bdwdth"], kernel["dur"],
                f, t, samp, plotflag=plotflag, kernel_lims=detect.finKernelLims,
            )

            Sxx_sub = Sxx[freq_inds, :][0]
            f_sub = f[freq_inds]

            times, values = detect.xcorr(
                t, f_sub, Sxx_sub, tvec, fvec, blue_kernel, plotflag=False, ylim=freqlim
            )

            analyzer_j = EventAnalyzer(
                times,
                values,
                utcstart_chunk - 0.5 * chunk_length,
                dur=event["dur"],
                prominence=event["prominence"],
                distance=event["distance"],
                rel_height=event["rel_height"],
            )

            if len(analyzer_j.df) >= 1:
                # Amplitude/SNR of calls from the Hilbert envelope in the call band
                sos = sig.butter(4, np.array(snr_limits), "bp", fs=samp, output="sos")
                filtered_data = sig.sosfiltfilt(sos, tr_filt.data)
                amplitude_envelope = abs(hilbert(filtered_data))
                seconds = np.arange(len(tr_filt.data)) / samp
                maxamp, ambient_snr, snr_vals, medamp = detect.amps_snr_timeseries(
                    seconds,
                    amplitude_envelope,
                    utcstart_chunk - 0.5 * chunk_length,
                    analyzer_j,
                    amps["dt_up"],
                    amps["dt_down"],
                    pad_length=amps["pad_length"],
                )

                # Optional low band to record earthquake-band SNR (Bryde's config
                # only; not used for detection filtering).
                if has_eq:
                    sos_eq = sig.butter(4, np.array(snr["eq_band"]), "bp", fs=samp, output="sos")
                    filtered_data_eq = sig.sosfiltfilt(sos_eq, tr_filt.data)
                    amplitude_envelope_eq = abs(hilbert(filtered_data_eq))
                    _, _, snr_eq, _ = detect.amps_snr_timeseries(
                        seconds,
                        amplitude_envelope_eq,
                        utcstart_chunk - 0.5 * chunk_length,
                        analyzer_j,
                        amps["dt_up"],
                        amps["dt_down"],
                        pad_length=amps["pad_length"],
                    )
            else:
                continue

            # Attach detection features for the current chunk
            n_rows = analyzer_j.df.shape[0]
            analyzer_j.df[cn.SNR] = snr_vals
            analyzer_j.df["ambient_snr"] = ambient_snr
            if has_eq:
                analyzer_j.df["eq_snr"] = snr_eq
            analyzer_j.df["db_amps"] = 20 * np.log10(maxamp)
            analyzer_j.df[cn.STATION_CODE] = np.repeat(tr_filt.stats.station, n_rows)
            analyzer_j.df[cn.NETWORK_CODE] = np.repeat(tr_filt.stats.network, n_rows)
            analyzer_j.df["peak_epoch"] = datetime_to_epoch(analyzer_j.df["peak_time"])
            analyzer_j.df["start_epoch"] = datetime_to_epoch(analyzer_j.df["start_time"])
            analyzer_j.df["end_epoch"] = datetime_to_epoch(analyzer_j.df["end_time"])
            analyzers_chunk.append(analyzer_j.df)

            # Multipath ranging via autocorrelation of the detection score
            data_starttime = tr_filt.stats.starttime
            utc_times = [data_starttime + ti for ti in times]
            timescount = int(round(chunk_length / (utc_times[1] - utc_times[0])))
            one_minute = int(60 / (utc_times[1] - utc_times[0]))
            numchunks = round(
                ((tr_filt.stats.endtime - tr_filt.stats.starttime) - chunk_length) / 60
            )

            for mp_iter in range(numchunks):
                startind = one_minute * mp_iter
                endind = one_minute * mp_iter + timescount
                times_sub = times[startind:endind]
                values_sub = values[startind:endind]
                start_utc = utc_times[startind]
                end_utc = utc_times[endind]

                j_df_sub = analyzer_j.df.loc[
                    (analyzer_j.df["peak_time"] >= start_utc)
                    & (analyzer_j.df["peak_time"] < end_utc)
                ]
                min_df_sub = analyzer_j.df.loc[
                    (analyzer_j.df["peak_time"] >= (start_utc + chunk_length / 2 - 30))
                    & (analyzer_j.df["peak_time"] < (end_utc - chunk_length / 2 + 30))
                ]

                if (
                    len(min_df_sub) >= ranging_thresholds["min_center"]
                    and len(j_df_sub) >= ranging_thresholds["min_window"]
                ):
                    # 10x-resolution detection score via cubic spline, then autocorrelate
                    det_timesnew = np.linspace(
                        min(times_sub), max(times_sub), len(times_sub) * 10
                    )
                    interp = interp1d(times_sub, values_sub, kind="cubic")
                    det_valuesnew = sig.detrend(interp(det_timesnew), type="constant")
                    corr = sig.correlate(det_valuesnew, det_valuesnew)
                    dt_res = det_timesnew[1] - det_timesnew[0]
                    autocorr_chunk = corr[
                        len(det_timesnew) - math.ceil(dt_up / dt_res):
                        len(det_timesnew) + math.ceil(dt_down / dt_res)
                    ] / max(corr)
                    dettimes_chunk = det_timesnew[0 : len(autocorr_chunk)]

                    mp_df_auto = pd.DataFrame(columns=cn.SCM_MULTIPATHS.columns)
                    dettimes_chunk = dettimes_chunk - min(dettimes_chunk)
                    mp_event = analyzer_j.mp_picker(
                        dettimes_chunk,
                        autocorr_chunk,
                        start_utc,
                        dur=multipath["dur"],
                        prominence=multipath["prominence"],
                        distance=multipath["distance"],
                        rel_height=multipath["rel_height"],
                    )
                    for _ in range(len(min_df_sub)):
                        mp_df_auto = pd.concat([mp_event, mp_df_auto], ignore_index=True)

                    min_df_sub = min_df_sub.reset_index(drop=True)
                    mp_df_auto = mp_df_auto.reset_index(drop=True)
                    min_df_sub = pd.concat([min_df_sub, mp_df_auto], axis=1)
                    d2 = {
                        "date": [start_utc + chunk_length / 2],
                        "epoch": datetime_to_epoch([start_utc + chunk_length / 2]),
                        "n_calls": [len(mp_df_auto)],
                        "sum_calls": [len(j_df_sub)],
                        "peaks": [np.median(j_df_sub["peak_signal"])],
                        "snr": [np.median(j_df_sub["snr"])],
                        "db_amps": [np.median(j_df_sub["db_amps"])],
                    }
                    if has_eq:
                        d2["low_snr"] = [np.mean(j_df_sub["eq_snr"])]
                    auto_df = pd.DataFrame(d2)
                    auto_df = pd.concat([auto_df, mp_df_auto.head(1)], axis=1)
                    auto_df_full.append(auto_df)

            analyzers.extend(analyzers_chunk)

            try:
                pd.concat(analyzers).to_csv(chunk_path, index=False)
                pd.concat(auto_df_full).to_csv(auto_path, index=False)
            except Exception:
                LOG.warning("Could not write intermediate CSVs for %s", station)
                continue

        utcstart_chunk = utcstart_chunk + day_length
        utcend_chunk = utcend_chunk + day_length

    if len(analyzers) == 0:
        LOG.warning("Detections dataframe empty for %s", station)
    elif analyzer_j is not None and len(analyzer_j.df) == 0:
        LOG.warning("No detections from current time window for %s", station)
    else:
        pd.concat(analyzers).to_csv(detection_path, index=False)
        LOG.info("Wrote %s", detection_path)


def _station_rows(table, site_range, station_filter):
    """Yield (index, row) for the selected stations from the info table."""
    start, stop = site_range
    for site_ind in range(start, stop):
        row = table.iloc[site_ind]
        if station_filter and row["Sites"] != station_filter:
            continue
        yield site_ind, row


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--station", help="Run only this station (default: all in site_range)")
    parser.add_argument("--verbose", action="store_true", help="Debug logging")
    args = parser.parse_args(argv)

    setup_logging(args.verbose)
    cfg = load_yaml(args.config)

    # Station table path is relative to the working directory (run from the
    # PythonCodes dir), matching the other data paths. It is the SAME shared
    # table for both species (see config comments).
    table = pd.read_csv(cfg["station_table"], parse_dates=["startdate", "enddate"])

    client = Client(cfg["client"])
    ss = cfg["sound_speed"]["water"]
    sed_speed = cfg["sound_speed"]["sediment"]
    output_dir = cfg.get("output_dir", ".")
    os.makedirs(output_dir, exist_ok=True)

    for site_ind, row in _station_rows(table, cfg["site_range"], args.station):
        station = row["Sites"]
        depth = row["Instrument Depth (m)"]
        thickness = row["Reflector depth (m)"] - depth

        # Estimate the multipath search window from the ranging model
        _, t0, _, _, _, _, mp_interp, _ = ranging.basic_ranging(
            depth, ss, sed_speed, thickness, plotflag=False
        )
        dt_down = max(np.subtract(mp_interp, t0)) + 0.2
        dt_up = cfg["download"]["dt_up_s"]

        out = cfg.get("output", {})
        det_template = out.get("detection_template", "{station}_mp.csv")
        auto_template = out.get("auto_template", "auto_{station}_mp.csv")
        chunk_path = os.path.join(output_dir, det_template.format(station=station))
        auto_path = os.path.join(output_dir, auto_template.format(station=station))

        LOG.info("Station %s (row %d): dt_up=%.2f dt_down=%.2f", station, site_ind, dt_up, dt_down)
        run_station(
            client=client,
            network=cfg["network"],
            station=station,
            location=cfg["location"],
            channel=row["Channel"],
            starttime=row["startdate"],
            endtime=row["enddate"],
            kernel=cfg["kernel"],
            spectrogram=cfg["spectrogram"],
            snr=cfg["snr"],
            event=cfg["event"],
            multipath=cfg["multipath"],
            ranging_thresholds=cfg["ranging"],
            amps=cfg["amps"],
            sound_speed=cfg["sound_speed"],
            response=cfg["response"],
            day_length=cfg["download"]["day_length_s"],
            chunk_length=cfg["download"]["chunk_length_s"],
            dt_up=dt_up,
            dt_down=dt_down,
            max_retries=cfg["download"]["max_retries"],
            chunk_path=chunk_path,
            auto_path=auto_path,
            detection_path=chunk_path,
            is_restart=cfg.get("is_restart", False),
        )


if __name__ == "__main__":
    main()
