"""Deterministic inputs shared by the golden-master capture script and tests.

These builders use only numpy so the exact same inputs can be fed to the
legacy code (when capturing fixtures) and to the refactored code (when
running the test suite). Nothing here depends on obspy or network access.
"""

import numpy as np

# Spectrogram / waveform parameters
FS = 100.0            # sampling rate (Hz)
DURATION_S = 40.0     # synthetic record length (s)

# Bryde's-call kernel parameters (from MP_Marianas_automation_Brydes.py)
KERNEL = {"F0": 37.0, "F1": 33.0, "BDWDTH": 2.0, "DUR": 3.0}

# plotwav call parameters used consistently across the pipeline
PLOTWAV = {
    "filt_type": "bandpass",
    "filt_freqlim": [10, 45],
    "filt_order": 2,
    "window_size": 0.8,
    "overlap": 0.95,
    "window_type": "hann",
}

# basic_ranging_model sample parameters (ENAM X08-like + degenerate t=0 case)
RANGING_CASES = [
    {"depth": 5271.0, "ss": 1512.0, "sed_speed": 1550.0, "t": 419.0},
    {"depth": 1000.0, "ss": 1500.0, "sed_speed": 1500.0, "t": 0.0},
]

CALL_ONSETS_S = (5.0, 12.0, 25.0)


def synthetic_waveform():
    """A reproducible waveform: low-level noise plus three descending chirps
    in the Bryde's-call band, matching the kernel sweep F0->F1 over DUR."""
    n = int(FS * DURATION_S)
    t = np.arange(n) / FS
    rng = np.random.default_rng(0)
    signal = 0.1 * rng.standard_normal(n)
    for onset in CALL_ONSETS_S:
        mask = (t >= onset) & (t < onset + KERNEL["DUR"])
        tt = t[mask] - onset
        inst_f = KERNEL["F0"] + (KERNEL["F1"] - KERNEL["F0"]) * (tt / KERNEL["DUR"])
        phase = 2 * np.pi * np.cumsum(inst_f) / FS
        signal[mask] += np.sin(phase)
    return signal


def synthetic_peak_series():
    """A clean series with three well-separated Gaussian peaks, used to
    exercise EventAnalyzer's peak detection and DataFrame construction."""
    t = np.arange(0.0, 60.0, 0.5)  # 0.5 s spacing
    vals = np.zeros_like(t)
    for center, amp in ((10.0, 1.0), (25.0, 0.8), (42.0, 1.2)):
        vals += amp * np.exp(-0.5 * ((t - center) / 1.5) ** 2)
    return t, vals


# EventAnalyzer parameters that yield a deterministic, non-empty detection frame
EVENT_PARAMS = {"dur": 1.0, "prominence": 0.2, "distance": 5.0, "rel_height": 0.8}
