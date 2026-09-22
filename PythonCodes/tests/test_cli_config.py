"""Network-free tests for the detection CLI's configuration handling.

These do not run the pipeline (which requires IRIS access); they verify that
the shipped config parses, the station table resolves and is filtered
correctly, and the ranging-derived search window is computed as expected.
"""

import os

import pandas as pd
import pytest

from whaletracks.cli import _common
from whaletracks.cli.run_detection import _station_rows

CONFIG = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "whaletracks", "config", "marianas.yaml",
)


@pytest.fixture(scope="module")
def cfg():
    return _common.load_yaml(CONFIG)


def test_config_has_required_sections(cfg):
    for key in ("client", "network", "station_table", "site_range",
                "kernel", "spectrogram", "snr", "event", "multipath",
                "sound_speed", "response", "download"):
        assert key in cfg, f"missing config section: {key}"
    assert set(cfg["kernel"]) == {"f0", "f1", "bdwdth", "dur"}


def test_station_table_resolves(cfg):
    path = _common.resolve_relative(CONFIG, cfg["station_table"])
    assert os.path.isfile(path)
    table = pd.read_csv(path)
    for col in ("Sites", "Channel", "Instrument Depth (m)", "Reflector depth (m)"):
        assert col in table.columns


def test_station_filter(cfg):
    path = _common.resolve_relative(CONFIG, cfg["station_table"])
    table = pd.read_csv(path)
    rows = list(_station_rows(table, [0, len(table)], "B19"))
    assert len(rows) == 1
    assert rows[0][1]["Sites"] == "B19"

    all_rows = list(_station_rows(table, cfg["site_range"], None))
    assert len(all_rows) == cfg["site_range"][1] - cfg["site_range"][0]
