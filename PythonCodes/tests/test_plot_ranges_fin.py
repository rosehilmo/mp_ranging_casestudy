"""Regression test for the fin-whale B20 timing->range step.

Reproduces the multipath ranging for the worked tutorial station (B20, fin
whales, CORTADO_TEST dataset) from the shipped autocorrelation timings and
checks it matches the committed output
``data/fin_whale/Marianas_auto_B20_CORTADO_TEST_v2.csv`` exactly. February 2013
onward is excluded (airgun-survey contamination). This locks the ranging step
that turns measured call timings into range CSVs.
"""

import os

import numpy as np
import pandas as pd
import pytest

from whaletracks.cli import _common
from whaletracks.cli.plot_ranges import estimate_ranges

PKG_ROOT = os.path.dirname(os.path.dirname(__file__))
CONFIG = os.path.join(PKG_ROOT, "whaletracks", "config", "ranges_fin.yaml")
COMMITTED = os.path.join(
    PKG_ROOT, "data", "fin_whale", "Marianas_auto_B20_CORTADO_TEST_v2.csv"
)

RANGE_COLS = [
    "range_D_MP1", "range_MP1_MP2", "range_MP2_MP3",
    "auto_max", "auto_snr", "auto_amp", "auto_count", "n_calls",
]


@pytest.mark.skipif(not os.path.isfile(COMMITTED), reason="committed B20 output not present")
def test_b20_cortado_ranges_match_committed(tmp_path):
    cfg = _common.load_yaml(CONFIG)
    # Resolve data directories to absolute paths so the test is CWD-independent.
    # The config's defaults are the B20 CORTADO_TEST inputs and the Feb-2013
    # airgun exclusion; the test uses them as-is.
    for key in ("bellhop_dir", "calls_dir"):
        cfg[key] = os.path.join(PKG_ROOT, cfg[key])
    cfg["output_dir"] = str(tmp_path)

    result = estimate_ranges(cfg, "B20", save=None, show=False)
    committed = pd.read_csv(COMMITTED)

    assert len(result) == len(committed)
    for col in RANGE_COLS:
        np.testing.assert_allclose(
            result[col].to_numpy(dtype=float),
            committed[col].to_numpy(dtype=float),
            rtol=1e-9,
            atol=1e-9,
        )
