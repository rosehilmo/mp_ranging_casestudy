"""Tests for the hypothesis-selection port (MATLABCodes/clean_group_ranges.m).

Synthetic structural tests pin the port's behaviour (grouping walk, group
qualification, supertrack construction, 3^n hypothesis assignment including
the single-group NaN quirk, per-call interpolation). The golden-master test
against a MATLAB reference output is skipped until the PI provides
``data/fin_whale/B20_grouped_ranges_CORTADO_TEST_matlab.csv`` (a
``clean_group_ranges.m`` run on ``Marianas_auto_B20_CORTADO_TEST_v2.csv`` —
see specs/002-hypothesis-selection).
"""

import os

import numpy as np
import pandas as pd
import pytest

from whaletracks.cli import _common
from whaletracks.detection.hypothesis_selection import (
    interpolate_call_ranges,
    select_hypotheses,
    selected_range,
)

PKG_ROOT = os.path.dirname(os.path.dirname(__file__))
GOLDEN = os.path.join(
    PKG_ROOT, "data", "fin_whale", "B20_grouped_ranges_CORTADO_TEST_matlab.csv"
)

BASE = pd.Timestamp("2012-04-01 00:00:00", tz="UTC")


def _rows(t0, n, r1_start, r2_offset, step_min=1.0, r1_step=0.1, auto_count=12):
    """n windows from t0, r1 walking gently upward (never a 1.6-km jump)."""
    rows = []
    for i in range(n):
        r1 = r1_start + i * r1_step
        rows.append({
            "time": t0 + pd.Timedelta(minutes=i * step_min),
            "range_D_MP1": r1,
            "range_MP1_MP2": r1 + r2_offset,
            "range_MP2_MP3": r1 + 2 * r2_offset,
            "auto_max": 5.0, "auto_snr": 10.0, "auto_amp": 100.0,
            "auto_count": auto_count, "n_calls": 3,
        })
    return rows


def _two_track_table():
    """Two qualifying groups 90 min apart (same supertrack) + noise rows."""
    rows = _rows(BASE, 12, r1_start=10.0, r2_offset=10.0)
    # 90-min gap: > 1 h (new group) but < 2 h (same supertrack). r2 offset
    # differs so hypothesis (1, 1) is the unique junction-cost minimum.
    rows += _rows(BASE + pd.Timedelta(minutes=101), 12, r1_start=11.3,
                  r2_offset=15.0)
    # Isolated noise rows: tiny groups, low counts -> never qualify.
    for h in (6, 10, 14):
        rows += _rows(BASE + pd.Timedelta(hours=h), 2, r1_start=20.0,
                      r2_offset=10.0, auto_count=1)
    # Out-of-scope rows: beyond 25 km, and saturated at the 40-km table edge.
    rows += _rows(BASE + pd.Timedelta(hours=20), 1, r1_start=30.0,
                  r2_offset=5.0)
    rows += _rows(BASE + pd.Timedelta(hours=21), 1, r1_start=40.0,
                  r2_offset=0.0)
    return pd.DataFrame(rows)


def test_two_groups_one_supertrack_best_hypothesis():
    out = select_hypotheses(_two_track_table())

    track_rows = out[out["use_track"]]
    assert len(track_rows) == 24  # both 12-row groups qualify, nothing else
    assert track_rows["groupnum"].nunique() == 2
    # One supertrack (90-min gap < 2 h), MATLAB id = first boundary index (1).
    assert set(track_rows["supertrack"]) == {1}
    # Junction cost is minimal for (MP1-Direct, MP1-Direct).
    assert set(track_rows["best_hypothesis"]) == {1.0}


def test_noise_and_out_of_scope_rows_excluded():
    out = select_hypotheses(_two_track_table())

    noise = out[out["auto_count"] == 1]
    assert not noise["use_track"].any()
    assert noise["best_hypothesis"].isna().all()

    beyond = out[out["range_D_MP1"] == 30.0]
    assert beyond["groupnum"].isna().all()  # 25-km filter
    saturated = out[out["auto_max"] == 5.0].tail(1)
    assert np.isnan(saturated["range_D_MP1"].iloc[0])  # 40 km -> NaN


def test_single_group_supertrack_gets_nan_hypothesis():
    out = select_hypotheses(pd.DataFrame(_rows(BASE, 12, 10.0, 10.0)))
    track_rows = out[out["use_track"]]
    assert len(track_rows) == 12
    assert track_rows["best_hypothesis"].isna().all()  # MATLAB quirk
    assert set(track_rows["supertrack"]) == {1}


def test_brydes_thresholds_qualify_smaller_groups():
    small = pd.DataFrame(_rows(BASE, 7, 10.0, 10.0, auto_count=3))
    fin = select_hypotheses(small)  # fin defaults: needs 12 rows
    assert not fin["use_track"].any()
    brydes = select_hypotheses(small, min_group_rows=7, min_mean_calls=2)
    assert brydes["use_track"].all()


def test_interpolate_call_ranges():
    grouped = pd.DataFrame({
        "time": [BASE, BASE + pd.Timedelta(minutes=10),
                 BASE + pd.Timedelta(minutes=20)],
        "range_D_MP1": [5.0, 6.0, 7.0],
        "range_MP1_MP2": [15.0, 16.0, 17.0],
        "range_MP2_MP3": [25.0, 26.0, 27.0],
        "use_track": True, "supertrack": 1.0, "best_hypothesis": 1.0,
    })
    calls = pd.DataFrame({
        "peak_time": [BASE + pd.Timedelta(minutes=5),
                      BASE + pd.Timedelta(hours=5)],
    })
    calls_out, grouped_out = interpolate_call_ranges(grouped, calls)
    np.testing.assert_allclose(calls_out["interp_range"].iloc[0], 5.5)
    assert np.isnan(calls_out["interp_range"].iloc[1])  # outside the span
    np.testing.assert_allclose(grouped_out["interp_range"], [5.0, 6.0, 7.0])


def test_selected_range_follows_hypothesis():
    grouped = pd.DataFrame({
        "range_D_MP1": [5.0, 5.0], "range_MP1_MP2": [15.0, 15.0],
        "range_MP2_MP3": [25.0, 25.0],
        "use_track": [True, True], "best_hypothesis": [1.0, 3.0],
    })
    np.testing.assert_allclose(selected_range(grouped), [5.0, 25.0])


def test_select_configs_parse():
    for name in ("select_fin.yaml", "select_brydes.yaml"):
        cfg = _common.load_yaml(
            os.path.join(PKG_ROOT, "whaletracks", "config", name)
        )
        for key in ("input_dir", "input_template", "output_dir",
                    "output_template", "filter", "grouping", "qualify",
                    "supertrack"):
            assert key in cfg, f"{name} missing {key}"


@pytest.mark.skipif(not os.path.isfile(GOLDEN),
                    reason="MATLAB reference output not yet provided (T107)")
def test_b20_golden_master_matches_matlab():
    """Golden master vs the PI's MATLAB clean_group_ranges.m run on B20."""
    raw = pd.read_csv(os.path.join(PKG_ROOT, "data", "fin_whale",
                                   "Marianas_auto_B20_CORTADO_TEST_v2.csv"))
    # The golden verifies PORT fidelity, so it uses the MATLAB script's own
    # hardcoded parameters (1.6 km grouping, 2 h track gap) — NOT the
    # published 1.5 km / 3 h that the fin config corrects to (KNOWN_ISSUES #7).
    out = select_hypotheses(raw, start="2012-03-01", range_jump_km=1.6,
                            supertrack_gap=pd.Timedelta(hours=2))
    ref = pd.read_csv(GOLDEN)
    assert len(out) == len(ref)
    np.testing.assert_array_equal(
        out["use_track"].to_numpy(), ref["use_track"].to_numpy().astype(bool)
    )
    for col in ("groupnum", "supertrack", "best_hypothesis"):
        np.testing.assert_allclose(
            out[col].to_numpy(dtype=float), ref[col].to_numpy(dtype=float),
            rtol=0, atol=0, equal_nan=True,
        )
