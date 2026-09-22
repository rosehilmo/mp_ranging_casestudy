"""Golden-master tests: the refactored library must reproduce the numeric
outputs captured from the legacy code (see scratchpad/capture_golden.py).

Fixtures live in tests/golden/. Inputs are built by golden_inputs.py so they
are identical to what was fed to the legacy code at capture time.
"""

import json
import os

import golden_inputs as gi
import numpy as np
import pytest
from obspy import UTCDateTime

GOLDEN = os.path.join(os.path.dirname(__file__), "golden")

RTOL = 1e-9
ATOL = 1e-10


@pytest.fixture(scope="module")
def fx():
    return np.load(os.path.join(GOLDEN, "fixtures.npz"))


@pytest.fixture(scope="module")
def scalars():
    with open(os.path.join(GOLDEN, "scalars.json")) as fh:
        return json.load(fh)


def _close(actual, expected):
    np.testing.assert_allclose(
        np.asarray(actual, dtype=float),
        np.asarray(expected, dtype=float),
        rtol=RTOL,
        atol=ATOL,
    )


# ---- common.util ----------------------------------------------------------
def test_util_complexify(scalars):
    from whaletracks.common import util

    got = util.complexifyString("(1,2);(3,-4)")
    _close([[c.real, c.imag] for c in got], scalars["complexify_nonempty"])
    assert util.complexifyString("") == []


def test_util_datestr_to_epoch(scalars):
    from whaletracks.common import util

    got = util.datestrToEpoch(
        ["1970-01-01T00:00:01.000Z", "2012-02-03T00:00:00.000000Z"]
    )
    _close(got, scalars["datestr_to_epoch"])


def test_util_datetime_to_epoch(scalars):
    from whaletracks.common import util

    got = util.datetimeToEpoch(
        [UTCDateTime("2012-02-03T00:00:00"), UTCDateTime("1970-01-01T00:00:10")]
    )
    _close(got, scalars["datetime_to_epoch"])


# ---- basic_ranging_model --------------------------------------------------
@pytest.mark.parametrize("i", [0, 1])
def test_basic_ranging(fx, i):
    from whaletracks.detection import basic_ranging_model as ranging

    case = gi.RANGING_CASES[i]
    out = ranging.basic_ranging(
        case["depth"], case["ss"], case["sed_speed"], case["t"], plotflag=False
    )
    names = ["distance", "t0", "t1", "t2", "t3", "d_interp", "mp_interp", "mp_interp2"]
    for name, val in zip(names, out, strict=True):
        _close(val, fx[f"ranging{i}_{name}"])


# ---- detect_calls signal pipeline ----------------------------------------
@pytest.fixture(scope="module")
def pipeline(fx):
    from whaletracks.detection import detect_calls as detect

    sig_data = gi.synthetic_waveform()
    f, t, Sxx = detect.plotwav(gi.FS, sig_data, plotflag=False, **gi.PLOTWAV)
    return detect, f, t, Sxx


def test_plotwav(pipeline, fx):
    _, f, t, Sxx = pipeline
    _close(f, fx["pw_f"])
    _close(t, fx["pw_t"])
    _close(Sxx, fx["pw_Sxx"])


def test_buildkernel(pipeline, fx):
    detect, f, t, Sxx = pipeline
    tvec, fvec_sub, kernel, freq_inds = detect.buildkernel(
        gi.KERNEL["F0"], gi.KERNEL["F1"], gi.KERNEL["BDWDTH"], gi.KERNEL["DUR"],
        f, t, gi.FS, plotflag=False, kernel_lims=detect.finKernelLims,
    )
    _close(tvec, fx["bk_tvec"])
    _close(fvec_sub, fx["bk_fvec_sub"])
    _close(kernel, fx["bk_kernel"])
    np.testing.assert_array_equal(np.asarray(freq_inds[0]), fx["bk_freq_inds"])


def test_xcorr(pipeline, fx):
    detect, f, t, Sxx = pipeline
    tvec, fvec_sub, kernel, _ = detect.buildkernel(
        gi.KERNEL["F0"], gi.KERNEL["F1"], gi.KERNEL["BDWDTH"], gi.KERNEL["DUR"],
        f, t, gi.FS, plotflag=False, kernel_lims=detect.finKernelLims,
    )
    xt, xv = detect.xcorr(t, f, Sxx, tvec, fvec_sub, kernel, plotflag=False)
    _close(xt, fx["xcorr_t"])
    _close(xv, fx["xcorr_v"])

    xlt, xlv = detect.xcorr_log(t, f, Sxx, tvec, fvec_sub, kernel, plotflag=False)
    _close(xlt, fx["xcorrlog_t"])
    _close(xlv, fx["xcorrlog_v"])


def test_spect_autocorr(pipeline, fx):
    detect, f, t, Sxx = pipeline
    at, av = detect.spect_autocorr(t, f, Sxx, seconds=10, plotflag=False, ylim=[10, 45])
    _close(at, fx["autocorr_t"])
    _close(av, fx["autocorr_v"])


# ---- event_analyzer -------------------------------------------------------
def test_event_analyzer(fx):
    from whaletracks.detection.event_analyzer import EventAnalyzer

    pk_t, pk_v = gi.synthetic_peak_series()
    start_chunk = UTCDateTime("2012-02-03T00:00:00")
    ea = EventAnalyzer(pk_t, pk_v, start_chunk, **gi.EVENT_PARAMS)
    df = ea.df
    _close([(x - start_chunk) for x in df["peak_time"]], fx["ea_peak_offset"])
    _close([(x - start_chunk) for x in df["start_time"]], fx["ea_start_offset"])
    _close([(x - start_chunk) for x in df["end_time"]], fx["ea_end_offset"])
    _close(df["peak_signal"], fx["ea_peak_signal"])
    _close(df["min_signal"], fx["ea_min_signal"])
    _close(df["duration"], fx["ea_duration"])
