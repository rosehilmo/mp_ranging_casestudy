"""Network-free tests for the detection CLI's configuration handling.

These do not run the pipeline (which requires IRIS access); they verify that
the shipped species configs parse, the Bryde's station table resolves and
filters correctly, and the ranging thresholds are well-formed.
"""

import os

import pandas as pd
import pytest

from whaletracks.cli import _common
from whaletracks.cli.run_detection import _station_rows

PKG_ROOT = os.path.dirname(os.path.dirname(__file__))
CONFIG_DIR = os.path.join(PKG_ROOT, "whaletracks", "config")
BRYDES = os.path.join(CONFIG_DIR, "detect_brydes.yaml")
FIN = os.path.join(CONFIG_DIR, "detect_fin.yaml")

REQUIRED = (
    "client", "network", "station_table", "site_range", "kernel", "spectrogram",
    "snr", "event", "multipath", "ranging", "amps", "sound_speed", "response",
    "download",
)


@pytest.mark.parametrize("path", [BRYDES, FIN])
def test_config_has_required_sections(path):
    cfg = _common.load_yaml(path)
    for key in REQUIRED:
        assert key in cfg, f"{os.path.basename(path)} missing section: {key}"
    assert set(cfg["kernel"]) == {"f0", "f1", "bdwdth", "dur"}
    assert set(cfg["ranging"]) == {"min_center", "min_window"}
    assert set(cfg["amps"]) == {"dt_up", "dt_down", "pad_length"}


def test_species_thresholds():
    # Bryde's: >=1 center, >=3 window; fin (published): >=2 center, >=10 window
    brydes = _common.load_yaml(BRYDES)["ranging"]
    fin = _common.load_yaml(FIN)["ranging"]
    assert (brydes["min_center"], brydes["min_window"]) == (1, 3)
    assert (fin["min_center"], fin["min_window"]) == (2, 10)


def test_fin_has_no_eq_band():
    # The published fin method does not use an earthquake-band discriminator.
    assert "eq_band" not in _common.load_yaml(FIN)["snr"]
    assert "eq_band" in _common.load_yaml(BRYDES)["snr"]


def test_shared_station_table():
    # Both species reference the same shared table (the 7 published OBS).
    brydes = _common.load_yaml(BRYDES)
    fin = _common.load_yaml(FIN)
    assert brydes["station_table"] == fin["station_table"]
    path = os.path.join(PKG_ROOT, brydes["station_table"])
    assert os.path.isfile(path)
    table = pd.read_csv(path)
    for col in ("Sites", "Channel", "Instrument Depth (m)", "Reflector depth (m)"):
        assert col in table.columns
    assert set(table["Sites"]) == {"B19", "B01", "B02", "B09", "B12", "B18", "B20"}


def test_station_filter():
    cfg = _common.load_yaml(BRYDES)
    table = pd.read_csv(os.path.join(PKG_ROOT, cfg["station_table"]))
    rows = list(_station_rows(table, [0, len(table)], "B19"))
    assert len(rows) == 1
    assert rows[0][1]["Sites"] == "B19"

    all_rows = list(_station_rows(table, cfg["site_range"], None))
    assert len(all_rows) == cfg["site_range"][1] - cfg["site_range"][0]
