"""Estimate whale ranges from autocorrelation multipath timings.

Side-effect-free core of the multipath ranging step, shared by the
``whaletracks-plot-ranges`` CLI and the fin-whale tutorial. For each
autocorrelation window it picks the strongest-amplitude multipath timing and
matches it against the modelled timing-vs-range curves (MP1-Direct, MP2-MP1,
MP3-MP2), returning one range estimate per qualifying window. This is the step
that turns the measured call timings (e.g. from station B19) into range CSVs.

The logic mirrors the published fin method (Hilmo & Wilcock 2024; Hilmo et al.
2025) and reproduces the legacy ``plot_ranges_calltimings_autocorr`` output.
"""

import numpy as np
import pandas as pd

# Output column order matches the committed Marianas_auto_{station}_v2.csv files.
RANGE_COLUMNS = [
    "time", "range_D_MP1", "range_MP1_MP2", "range_MP2_MP3",
    "auto_max", "auto_snr", "auto_amp", "auto_count", "n_calls",
]


def bellhop_timings(bellhop_df):
    """Consecutive-arrival timing curves from a BELLHOP ray table.

    Returns ``(distance, mp_1_timing, mp_2_timing, mp_3_timing)``: the modelled
    range axis (metres) and the MP1-Direct, MP2-MP1 and MP3-MP2 arrival-time
    spacings (seconds), each indexed by range step.
    """
    distance = bellhop_df["interp_r"]
    t0, t1, t2, t3 = (
        bellhop_df["interp_d"], bellhop_df["interp_mp1"],
        bellhop_df["interp_mp2"], bellhop_df["interp_mp3"],
    )
    return distance, np.subtract(t1, t0), np.subtract(t2, t1), np.subtract(t3, t2)


def _as_bound(value, like):
    """Coerce a date bound to a Timestamp matching the tz of the ``like`` series."""
    ts = pd.Timestamp(value)
    tz = like.dt.tz
    if tz is not None and ts.tz is None:
        ts = ts.tz_localize(tz)
    return ts


def estimate_ranges_from_timings(
    auto_df, calltimes, distance, mp_1_timing, mp_2_timing, mp_3_timing,
    reflectivity=False, mp_1_sub=None, valid_start=None, valid_end=None,
):
    """Match autocorrelation timings to ranges; return a ranges DataFrame.

    Parameters
    ----------
    auto_df : DataFrame
        Per-window autocorrelation table with columns ``arrival_1..5``,
        ``amp_2..5``, ``peaks``, ``snr``, ``db_amps``, ``sum_calls``,
        ``n_calls`` and ``date``.
    calltimes : array-like of datetime
        Detection peak times; a window is ranged only if at least one call
        falls in its centre minute (date +/- 30 s).
    distance : Series
        Modelled range axis (metres), indexed 0..N-1 to match the timing curves.
    mp_1_timing, mp_2_timing, mp_3_timing : array-like
        Modelled MP1-Direct, MP2-MP1 and MP3-MP2 spacing curves (seconds).
    reflectivity : bool
        If True and ``mp_1_sub`` is given, use the subsurface-reflection curve
        for close ranges (< 110 m match), as in the reflectivity model.
    mp_1_sub : array-like or None
        Optional subsurface-reflection timing curve.
    valid_start, valid_end : datetime-like or None
        Optional half-open date bounds ``[valid_start, valid_end)`` on the
        window time. Used to exclude periods where ranging is unreliable — e.g.
        airgun-survey intervals that corrupt the multipath timings.

    Returns
    -------
    DataFrame with columns :data:`RANGE_COLUMNS` — one row per qualifying window.
    """
    dates = [pd.to_datetime(d) for d in auto_df["date"].tolist()]
    times, r_d_mp1, r_mp1_mp2, r_mp2_mp3 = [], [], [], []
    auto_max, auto_snr, auto_amp, auto_count, center_calls = [], [], [], [], []

    for row in range(len(auto_df)):
        df = auto_df.iloc[row]
        date = dates[row]
        window = calltimes[
            (calltimes > date - pd.Timedelta(seconds=30))
            & (calltimes < date + pd.Timedelta(seconds=30))
        ]
        if len(window) == 0:
            continue

        # Spacings of the four later arrivals from the first; use the strongest.
        timings = [df[f"arrival_{k}"] - df["arrival_1"] for k in (2, 3, 4, 5)]
        amps = [df[f"amp_{k}"] for k in (2, 3, 4, 5)]
        mp_timing = timings[amps.index(max(amps))]

        near1 = [abs(mp - mp_timing) for mp in mp_1_timing]
        near2 = [abs(mp - mp_timing) for mp in mp_2_timing]
        near3 = [abs(mp - mp_timing) for mp in mp_3_timing]
        best_distance = distance[near1.index(min(near1))]
        best_distance_2 = distance[near2.index(min(near2))]
        best_distance_3 = distance[near3.index(min(near3))]

        if best_distance < 110 and reflectivity and mp_1_sub is not None:
            near_sub = [abs(mp - mp_timing) for mp in mp_1_sub]
            best_distance = distance[near_sub.index(min(near_sub))]

        times.append(date)
        r_d_mp1.append(best_distance / 1000)
        r_mp1_mp2.append(best_distance_2 / 1000)
        r_mp2_mp3.append(best_distance_3 / 1000)
        auto_max.append(df["peaks"])
        auto_snr.append(df["snr"])
        auto_amp.append(df["db_amps"])
        auto_count.append(df["sum_calls"])
        center_calls.append(df["n_calls"])

    out = pd.DataFrame({
        "time": times,
        "range_D_MP1": r_d_mp1,
        "range_MP1_MP2": r_mp1_mp2,
        "range_MP2_MP3": r_mp2_mp3,
        "auto_max": auto_max,
        "auto_snr": auto_snr,
        "auto_amp": auto_amp,
        "auto_count": auto_count,
        "n_calls": center_calls,
    })
    if valid_start is not None:
        out = out[out["time"] >= _as_bound(valid_start, out["time"])]
    if valid_end is not None:
        out = out[out["time"] < _as_bound(valid_end, out["time"])]
    return out.reset_index(drop=True)
