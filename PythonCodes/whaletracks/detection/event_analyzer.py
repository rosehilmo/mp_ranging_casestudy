#!/usr/bin/env python3
"""
Detect events (whale calls) in a detection-score time series via
``scipy.signal.find_peaks`` and expose the results as pandas DataFrames.

Created on Tue Jan 28 14:15:18 2020
@author: wader
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.signal as sig

from whaletracks.common import constants as cn

# Reference call parameters (blue/fin whale tuning notes):
#   b-call  dur=5,  rel_height=.7 prominence=.5 wlen=60 s
#   a-call  dur=70, rel_height=.9 prominence=.3 wlen=2 min distance=30
#   fin-call dur=.5, rel_height=.3 prominence=.6 wlen=60 s distance=18
SECONDS_IN_MINUTE = 60
EXCLUDED_COLUMNS = [cn.THRESHOLD, cn.STATION_CODE, cn.NETWORK_CODE]


class EventAnalyzer:
    def __init__(
        self, times, values, start_chunk, dur=1, prominence=0.6, distance=18, rel_height=0.8
    ):
        """
        :param list-float times: offsets in seconds
        :param list-float values: values at times
        :param UTCDateTime start_chunk: start time of chunk
        :param float dur: duration in seconds of call (default for blue whale)
        """
        self.times = [start_chunk + t for t in times]
        self.values = values
        self.start_chunk = start_chunk
        samples_per_second = 1 / (self.times[1] - self.times[0])
        peak_indices, peak_properties = sig.find_peaks(
            self.values,
            distance=distance * samples_per_second,
            width=dur * samples_per_second,
            prominence=prominence,
            wlen=SECONDS_IN_MINUTE * samples_per_second,
            rel_height=rel_height,
        )

        self.df = self._make_detection_df(peak_indices, peak_properties, self.times)
        self.df[cn.THRESHOLD] = prominence

    @staticmethod
    def _empty_detection_dict():
        return {k: [] for k in cn.SCM_DETECTION.columns if k not in EXCLUDED_COLUMNS}

    def _make_detection_df(self, peak_indices, peak_properties, times):
        """Build a detection DataFrame from find_peaks output.

        :param peak_indices: indices of detected peaks
        :param peak_properties: properties dict returned by find_peaks
        :param times: absolute times corresponding to the value series
        :return pd.DataFrame: detection frame (excluding EXCLUDED_COLUMNS)
        """
        dct = self._empty_detection_dict()
        left = peak_properties["left_ips"].astype(int)
        right = peak_properties["right_ips"].astype(int)
        for index in range(len(peak_indices)):
            dct[cn.PEAK_TIME].append(times[peak_indices[index]])
            dct[cn.PEAK_SIGNAL].append(peak_properties["prominences"][index])
            dct[cn.START_TIME].append(times[left[index]])
            dct[cn.END_TIME].append(times[right[index]])
            dct[cn.MIN_SIGNAL].append(peak_properties["width_heights"][index])
            dct[cn.DURATION].append(times[right[index]] - times[left[index]])

        n = len(peak_indices)
        for key in (cn.PEAK_EPOCH, cn.START_EPOCH, cn.END_EPOCH, cn.SNR, cn.SNR_AMBIENT, cn.SNR_EQ):
            dct[key] = list(np.repeat(None, n))

        return pd.DataFrame(dct)

    def mp_picker(
        self, times, values, utcstart_chunk, dur=0.5, prominence=0.1, distance=0.1, rel_height=0.5
    ):
        """
        :param list-float times: offsets in seconds
        :param list-float values: values at times
        :param UTCDateTime utcstart_chunk: start time of chunk
        :param float dur: duration in seconds of call
        """
        samples_per_second = 1 / (times[1] - times[0])
        peak_indices, peak_properties = sig.find_peaks(
            values,
            distance=distance * samples_per_second,
            width=(dur / 2) * samples_per_second,
            prominence=prominence,
            wlen=SECONDS_IN_MINUTE * samples_per_second,
            rel_height=rel_height,
        )

        for ind in range(len(peak_properties["prominences"])):
            peak_properties["prominences"][ind] += max(
                values[peak_properties["left_bases"][ind]],
                values[peak_properties["right_bases"][ind]],
            )

        return self.make_multipath_df(peak_indices, peak_properties, times, values, utcstart_chunk)

    def make_multipath_df(self, peak_indices, peak_properties, times, values, utcstart_chunk):
        """Build a multipath-arrival DataFrame (top-5 arrivals by amplitude).

        :param peak_indices: indices of detected peaks
        :param peak_properties: properties dict returned by find_peaks
        :return pd.DataFrame: single-row multipath frame
        """
        dct = self._empty_detection_dict()
        left = peak_properties["left_ips"].astype(int)
        right = peak_properties["right_ips"].astype(int)
        for index in range(len(peak_indices)):
            dct[cn.PEAK_TIME].append(times[peak_indices[index]])
            dct[cn.PEAK_SIGNAL].append(peak_properties["prominences"][index])
            dct[cn.START_TIME].append(times[left[index]])
            dct[cn.END_TIME].append(times[right[index]])
            dct[cn.MIN_SIGNAL].append(peak_properties["width_heights"][index])
            dct[cn.DURATION].append(times[right[index]] - times[left[index]])

        n = len(peak_indices)
        for key in (cn.PEAK_EPOCH, cn.START_EPOCH, cn.END_EPOCH, cn.SNR, cn.SNR_AMBIENT, cn.SNR_EQ):
            dct[key] = list(np.repeat(None, n))

        event_df = pd.DataFrame(dct)
        event_peaksort = event_df.sort_values(by=["peak_signal"], ascending=False)[0:5]
        event_timesort = event_peaksort.sort_values(by=["peak_time"])
        arrivals = event_timesort["peak_time"].values.tolist()
        time_diff = event_timesort[cn.DURATION].values.tolist()
        amplitudes = event_timesort["peak_signal"].values.tolist()
        nonelist = list(np.repeat(None, 5 - len(arrivals)))
        arrivals = arrivals + nonelist
        amplitudes = amplitudes + nonelist
        time_diff = time_diff + nonelist

        mp_dct = {k: [] for k in cn.SCM_MULTIPATHS.columns if k not in EXCLUDED_COLUMNS}
        for i, col in enumerate(
            (cn.ARRIVAL_1, cn.ARRIVAL_2, cn.ARRIVAL_3, cn.ARRIVAL_4, cn.ARRIVAL_5)
        ):
            mp_dct[col].append(arrivals[i])
        for i, col in enumerate((cn.AMP_1, cn.AMP_2, cn.AMP_3, cn.AMP_4, cn.AMP_5)):
            mp_dct[col].append(amplitudes[i])
        for i, col in enumerate((cn.ERR_1, cn.ERR_2, cn.ERR_3, cn.ERR_4, cn.ERR_5)):
            mp_dct[col].append(time_diff[i])
        return pd.DataFrame(mp_dct)

    def plot(self, is_plot=True):
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot(self.times, self.values)
        ax.plot(self.df.peak_time, self.df.peak_signal, "x")
        plt.hlines(self.df.min_signal, self.df.start_time, self.df.end_time, color="C2")
        if is_plot:
            plt.show(block=True)


# Backward-compatible aliases (legacy method names)
EventAnalyzer._makeDetectionDF = EventAnalyzer._make_detection_df
EventAnalyzer.makeMultipathDF = EventAnalyzer.make_multipath_df
