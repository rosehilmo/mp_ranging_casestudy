"""Shared helpers for the whaletracks command-line entry points."""

import logging
import os

import yaml

LOG = logging.getLogger("whaletracks")


def setup_logging(verbose=False):
    """Configure root logging for a CLI run."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )


def load_yaml(path):
    """Load a YAML config file into a dict."""
    with open(path) as fh:
        return yaml.safe_load(fh)


def resolve_relative(config_path, value):
    """Resolve ``value`` relative to the directory holding ``config_path``.

    Absolute paths are returned unchanged.
    """
    if os.path.isabs(value):
        return value
    return os.path.join(os.path.dirname(os.path.abspath(config_path)), value)
