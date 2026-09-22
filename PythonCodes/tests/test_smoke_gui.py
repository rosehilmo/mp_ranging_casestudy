"""Import-smoke tests for the interactive GUI CLIs and the manual-picking lib.

These never touch the network or open a GUI; they only verify that the modules
import, expose a ``main``, respond to ``--help``, and that their YAML configs
parse.
"""

import os

import pytest

from whaletracks.cli import _common

CONFIG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "whaletracks", "config"
)


def test_manual_picking_imports():
    from whaletracks.detection import manual_picking

    for name in ("plotwav", "freq_analysis", "get_snr", "find_nearest",
                 "datetime_to_epoch"):
        assert hasattr(manual_picking, name), f"manual_picking missing {name}"


@pytest.mark.parametrize("module_name", ["verify_calls", "manual_picker"])
def test_cli_has_main_and_help(module_name):
    import importlib

    mod = importlib.import_module(f"whaletracks.cli.{module_name}")
    assert hasattr(mod, "main")
    # argparse exits with code 0 on --help
    with pytest.raises(SystemExit) as exc:
        mod.main(["--help"])
    assert exc.value.code == 0


@pytest.mark.parametrize("config_name", ["verify_calls.yaml", "manual_picker.yaml"])
def test_gui_configs_parse(config_name):
    cfg = _common.load_yaml(os.path.join(CONFIG_DIR, config_name))
    assert isinstance(cfg, dict)
    for key in ("client", "network", "station_list", "response", "spectrogram"):
        assert key in cfg, f"{config_name} missing {key}"
