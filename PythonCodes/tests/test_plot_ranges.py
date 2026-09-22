"""Regression test for the range-estimation CLI against committed output.

Runs estimate_ranges() for station B01 (bellhop mode) and checks that the
computed range columns match the committed legacy output
MarianasAutoFiles/Marianas_auto_B01_v2.csv exactly. This proves the refactor
preserves the scientific output; only float string-repr of passthrough
metadata columns changed between pandas versions, so we compare the range
columns numerically.
"""

import os

import numpy as np
import pandas as pd
import pytest

from whaletracks.cli import _common
from whaletracks.cli.plot_ranges import estimate_ranges

PKG_ROOT = os.path.dirname(os.path.dirname(__file__))
CONFIG = os.path.join(PKG_ROOT, "whaletracks", "config", "ranges_brydes.yaml")
LEGACY_OUT = os.path.join(
    PKG_ROOT, "data", "brydes_whale", "MarianasAutoFiles", "Marianas_auto_B01_v2.csv"
)

RANGE_COLS = ["range_D_MP1", "range_MP1_MP2", "range_MP2_MP3"]


@pytest.mark.skipif(not os.path.isfile(LEGACY_OUT), reason="legacy B01 output not present")
def test_b01_ranges_match_legacy(tmp_path):
    cfg = _common.load_yaml(CONFIG)
    # Resolve data directories to absolute paths so the test is CWD-independent.
    for key in ("bellhop_dir", "calls_dir"):
        cfg[key] = os.path.join(PKG_ROOT, cfg[key])
    cfg["output_dir"] = str(tmp_path)

    result = estimate_ranges(cfg, "B01", save=None, show=False)
    legacy = pd.read_csv(LEGACY_OUT)

    assert len(result) == len(legacy)
    for col in RANGE_COLS:
        np.testing.assert_allclose(
            result[col].to_numpy(dtype=float),
            legacy[col].to_numpy(dtype=float),
            rtol=1e-9,
            atol=1e-9,
        )
