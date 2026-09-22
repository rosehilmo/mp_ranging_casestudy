"""Helper functions for the interactive manual-picking workflow.

These spectrogram / SNR / frequency routines are tailored to manual picking
and differ numerically from the similarly named functions in
``detect_calls`` (different default filter order, filtering method, SNR
windowing, and ``freq_analysis`` signature). They are therefore kept separate
here rather than merged into ``detect_calls``. Cleaned from the legacy
``detectBrydes_manual.py``; math preserved exactly.
"""

from datetime import datetime

import matplotlib.colors as color
import matplotlib.pyplot as plt
import numpy as np
import scipy.signal as sig

_SECONDS_IN_DAY = 86400
_EPOCH_START = datetime.strptime("1970-01-01T00:00:00.00Z", "%Y-%m-%dT%H:%M:%S.%fZ")


def datetime_to_epoch(utcdatetime_list):
    """Convert a list of obspy ``UTCDateTime`` objects to epoch seconds.

    :param list utcdatetime_list: list of ``UTCDateTime`` objects
    :return list: seconds elapsed since 1970-01-01
    """
    epochlist = []
    for utc in utcdatetime_list:
        epoch_delta = utc.datetime - _EPOCH_START
        epoch_j = (
            epoch_delta.days * _SECONDS_IN_DAY
            + epoch_delta.seconds
            + epoch_delta.microseconds / 1000000
        )
        epochlist.append(epoch_j)
    return epochlist


def find_nearest(array, value):
    """Return the index of the array element nearest to ``value``."""
    array = np.asarray(array)
    return (np.abs(array - value)).argmin()


def get_snr(
    picks,
    t,
    f,
    Sxx,
    utcstart_chunk,
    snr_limits=(12, 16),
    snr_calllength=4,
    snr_freqwidth=0.6,
    dur=10,
):
    """Compute call SNR and ambient (pre-call) SNR for a list of manual picks.

    :param picks: list of pick times (UTCDateTime)
    :param t: spectrogram time offsets (s)
    :param f: spectrogram frequencies (Hz)
    :param Sxx: spectrogram amplitudes
    :param utcstart_chunk: start time of the chunk (UTCDateTime)
    :return tuple: (snr, ambient_snr) lists in dB
    """
    peak_times = picks
    snr = []
    freq_inds = np.where(np.logical_and(f >= min(snr_limits), f <= max(snr_limits)))
    Sxx_sub = Sxx[freq_inds, :][0]
    f = f[freq_inds]

    med_noise = np.median(Sxx_sub)
    utc_t = [utcstart_chunk + j for j in t]
    snr_t_int = np.int64((snr_calllength) / (utc_t[1] - utc_t[0]))
    for utc_time in peak_times:
        t_peak_ind = find_nearest(utc_t, utc_time)
        Sxx_t_inds1 = list(range(t_peak_ind, t_peak_ind + snr_t_int))
        Sxx_t_inds = [x for x in Sxx_t_inds1 if x < len(t)]
        Sxx_t_sub = Sxx_sub[:, Sxx_t_inds]
        db_max = np.max(Sxx_sub[:, t_peak_ind])
        max_loc = np.where(Sxx_sub[:, t_peak_ind] == db_max)
        freq_max = f[max_loc]
        f_inds = np.where(
            np.logical_and(f >= freq_max - snr_freqwidth / 2, f <= freq_max + snr_freqwidth / 2)
        )
        Sxx_tf_sub = Sxx_t_sub[f_inds, :]
        call_noise = np.median(Sxx_tf_sub)
        snr = snr + [10 * np.log10(call_noise / med_noise)]

    # Get SNR of `dur` seconds of noise preceding the call
    start_times = picks
    noise_t_int = np.int64((dur) / (utc_t[1] - utc_t[0]))
    start_snr = []
    for utc_time in start_times:
        t_peak_ind = find_nearest(utc_t, utc_time)
        Sxx_t_inds1 = list(range(t_peak_ind - noise_t_int, t_peak_ind))
        Sxx_t_inds = [x for x in Sxx_t_inds1 if x >= 0]
        Sxx_t_sub = Sxx_sub[:, Sxx_t_inds]
        ambient_noise = np.median(Sxx_t_sub)
        start_snr = start_snr + [10 * np.log10(ambient_noise / med_noise)]

    ambient_snr = start_snr
    return snr, ambient_snr


def default_scale_function(Sxx):
    """Default spectrogram color limits: median to median + 2 std (in dB)."""
    vmin = np.median(10 * np.log10(Sxx)) + 0 * np.std(10 * np.log10(Sxx))
    vmax = np.median(10 * np.log10(Sxx)) + 2 * np.std(10 * np.log10(Sxx))
    return vmin, vmax


def plotwav(
    samp,
    data,
    filt_type="bandpass",
    filt_freqlim=(12, 18),
    filt_order=4,
    window_size=4,
    overlap=0.95,
    window_type="hann",
    plotflag=True,
    scale_func=default_scale_function,
    ylim=(12, 18),
):
    """Calculate a spectrogram (and optionally plot it).

    Manual-picking variant: uses a ``filtfilt`` Butterworth filter (order 4 by
    default) rather than the ``sosfiltfilt`` path in ``detect_calls.plotwav``.

    :param float samp: sampling rate
    :param numpy.array data: data to process
    :param string filt_type: filter type (highpass, lowpass, bandpass, etc.)
    :param filt_freqlim: frequency limits of filter
    :param int filt_order: order of filter
    :param float window_size: spectrogram window size (seconds)
    :param float overlap: overlap ratio of spectrogram window
    :param string window_type: spectrogram window type
    :param bool plotflag: if True, make plots
    :param function scale_func: single-arg Sxx -> (vmin, vmax)
    :param ylim: frequency bounds for spectrogram plot
    :return list: [f, t, Sxx] (frequencies, times, power)
    """
    PLT_TIMESERIES = 1
    FIGSIZE = [9, 3]
    FILTER_OFFSET = 10

    # filter data to spectral bands where B-call is
    [b, a] = sig.butter(filt_order, np.array(filt_freqlim) / samp, filt_type, "ba")
    filtered_data = sig.filtfilt(b, a, data)

    datalength = data.size
    times = np.arange(datalength) / samp

    # plot timeseries on upper axis
    if plotflag:
        plt.figure(PLT_TIMESERIES, figsize=FIGSIZE)
        plt.subplot(211)
        plt.plot(times[FILTER_OFFSET:], filtered_data[FILTER_OFFSET:])
        plt.axis(
            [
                min(times),
                max(times),
                min(filtered_data[FILTER_OFFSET:]),
                max(filtered_data[FILTER_OFFSET:]),
            ]
        )
        plt.xlabel("Seconds")
        plt.ylabel("Amplitude")

    # spectrogram on lower axis
    [f, t, Sxx] = sig.spectrogram(
        filtered_data,
        int(samp),
        window_type,
        int(samp * window_size),
        int(samp * window_size * overlap),
    )

    if plotflag:
        cmap = plt.get_cmap("magma")
        vmin, vmax = scale_func(Sxx)
        norm = color.Normalize(vmin=vmin, vmax=vmax)
        plt.subplot(212)
        plt.pcolormesh(t, f, 10 * np.log10(Sxx), cmap=cmap, norm=norm)
        plt.ylabel("Frequency [Hz]")
        plt.xlabel("Time [sec]")
        plt.ylim(ylim)
        plt.show()

    return [f, t, Sxx]


def freq_analysis(picks_t, calltype, t, f, Sxx, utcstart_chunk, freq_window_b=(35, 40)):
    """Estimate peak frequency and spread for each 'B' call pick.

    :param picks_t: list of pick times (UTCDateTime)
    :param calltype: list of call-type labels aligned with ``picks_t``
    :param t: spectrogram time offsets (s)
    :param f: spectrogram frequencies (Hz)
    :param Sxx: spectrogram amplitudes
    :param utcstart_chunk: start time of the chunk (UTCDateTime)
    :return tuple: (peak_freqs, peak_stds)
    """
    peak_freqs = []
    peak_stds = []

    freq_inds = np.where(np.logical_and(f >= min(freq_window_b), f <= max(freq_window_b)))
    Sxx_sub = Sxx[freq_inds, :][0]
    f_b = f[freq_inds]
    utc_t = [utcstart_chunk + j for j in t]
    utc_array = np.array(utc_t)

    for k in range(0, len(picks_t)):  # for peak freq
        if calltype[k] == "B":
            starttime = picks_t[k] + 1
            endtime = picks_t[k] + 5
            callbool = (utc_array < endtime) & (utc_array > starttime)
            inds = np.array(list(range(len(callbool))))
            callinds = inds[callbool]
            call_times = utc_array[callbool]
            Sxx_total_sub = Sxx_sub[:, callinds]
            farray = np.tile(f_b, (len(call_times), 1))
            peak_freq = np.sum(np.multiply(farray.T, Sxx_total_sub)) / np.sum(Sxx_total_sub)
            peak_freqs = peak_freqs + [peak_freq]
            peak_std = np.sum(
                np.multiply(np.power(np.subtract(farray.T, np.mean(farray)), 2), Sxx_total_sub)
            ) / np.sum(Sxx_total_sub)
            peak_stds = peak_stds + [peak_std]

    return peak_freqs, peak_stds


# Backward-compatible alias (legacy camelCase name)
datetimeToEpoch = datetime_to_epoch
