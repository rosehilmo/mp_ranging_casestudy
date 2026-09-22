"""Utilities for the whale project: string/time conversions.

Public functions use snake_case names; the original camelCase names are kept
as aliases at the bottom of the module for backward compatibility.
"""

import ast
from datetime import datetime

_EPOCH_START = datetime.strptime("1970-01-01T00:00:00.00Z", "%Y-%m-%dT%H:%M:%S.%fZ")
_SECONDS_IN_DAY = 86400


def complexify_string(stg, separator=";"):
    """Convert a separated string of ``(real, imag)`` pairs into complex numbers.

    :param str stg: string of complex numbers, e.g. ``"(1,2);(3,-4)"``
    :param str separator: delimiter between pairs
    :return list: list of ``complex`` values (empty if ``stg`` is empty)
    """
    splits = stg.split(separator)
    if len(splits[0]) > 0:
        pairs = [ast.literal_eval(s) for s in splits]
        return [complex(re, im) for re, im in pairs]
    return []


def _delta_to_epoch(delta):
    """Seconds elapsed for a ``timedelta`` since the Unix epoch."""
    return delta.days * _SECONDS_IN_DAY + delta.seconds + delta.microseconds / 1_000_000


def datestr_to_epoch(datestrs, dateformat="%Y-%m-%dT%H:%M:%S.%fZ"):
    """Convert datestrings in UTCDateTime format to epoch seconds.

    :param list datestrs: list of datestrings
    :param str dateformat: format accepted by ``datetime.strptime``
    :return list: seconds elapsed since 1970-01-01
    """
    return [_delta_to_epoch(datetime.strptime(s, dateformat) - _EPOCH_START) for s in datestrs]


def datetime_to_epoch(utcdatetime_list):
    """Convert a list of obspy ``UTCDateTime`` objects to epoch seconds.

    :param list utcdatetime_list: list of ``UTCDateTime`` objects
    :return list: seconds elapsed since 1970-01-01
    """
    return [_delta_to_epoch(utc.datetime - _EPOCH_START) for utc in utcdatetime_list]


def add_epoch_columns(dataframe):
    """Add a ``<name>_EPOCH`` column for every ``<name>_TIME`` column in place."""
    ending = "_TIME"
    for col in dataframe.columns:
        if ending in col:
            front = col[: len(col) - len(ending)]
            dataframe[f"{front}_EPOCH"] = datestr_to_epoch(dataframe[col])
    return dataframe


# Backward-compatible aliases (legacy camelCase names)
complexifyString = complexify_string
datestrToEpoch = datestr_to_epoch
datetimeToEpoch = datetime_to_epoch
addEpochColumns = add_epoch_columns
