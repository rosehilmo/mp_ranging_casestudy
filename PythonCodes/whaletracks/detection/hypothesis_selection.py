"""Semi-automated multipath hypothesis selection.

Turns the raw ranging output (three candidate ranges per window, one per timing
hypothesis) into grouped whale tracks with a best hypothesis per group, and
removes spurious ranges that fail the track criteria. This is the semi-automated
selection step of Hilmo et al. (2025).

Behaviours worth knowing (all deliberate — see ``KNOWN_ISSUES.md``):

- the supertrack boundary group belongs to the earlier segment, and the
  junction across a boundary is never scored;
- single-group supertracks are left unassigned (``best_hypothesis = NaN``):
  a lone group has no neighbour to score against, so it is deferred to review;
- hypothesis combinations are enumerated with the first group varying slowest,
  and ties break to the first minimum;
- combination costs containing NaN ranges are ignored; if every combination is
  NaN the first is taken;
- segments with more than ``max_segment_groups`` groups are split at their
  midpoint, halves rounded away from zero.

The interactive analyst verification (accept / override / reject per group)
stays a manual step — see the ``--review`` mode of ``whaletracks-select``.
"""

import numpy as np
import pandas as pd

#: Columns appended by :func:`select_hypotheses`.
SELECTION_COLUMNS = ["groupnum", "use_track", "supertrack", "best_hypothesis"]

_HYPOTHESIS_RANGE = {1: "range_D_MP1", 2: "range_MP1_MP2", 3: "range_MP2_MP3"}

#: Published fin parameters (Hilmo et al. 2025): ranges within 1.5 km and 1 h
#: are grouped; groups less than 3 h apart are linked into tracks. (The Bryde's
#: config uses 1.6 km / 2 h — see KNOWN_ISSUES.md, "Fin-whale profile" →
#: *Selection grouping/track parameters*.)
ONE_HOUR = pd.Timedelta(hours=1)
THREE_HOURS = pd.Timedelta(hours=3)


def _round_half_up(x):
    """Round halves away from zero (inputs here are positive)."""
    return int(np.floor(x + 0.5))


def filter_ranges(ranges_df, start=None, max_range_km=25.0,
                  min_window_calls=1, saturation_km=40.0):
    """Step 1: time cut, 40-km saturation -> NaN, 25-km / call-count filter.

    Returns ``(working, mask)``: the (possibly time-cut) full table with
    saturated ranges set to NaN, and the boolean mask of rows that qualify for
    grouping (``range_D_MP1 < max_range_km`` and ``auto_count >=
    min_window_calls``; NaN ranges drop out of the comparison).
    """
    working = ranges_df.copy()
    working["time"] = pd.to_datetime(working["time"])
    if start is not None:
        bound = pd.Timestamp(start)
        if working["time"].dt.tz is not None and bound.tz is None:
            bound = bound.tz_localize(working["time"].dt.tz)
        working = working[working["time"] > bound].reset_index(drop=True)

    for col in ("range_D_MP1", "range_MP1_MP2", "range_MP2_MP3"):
        working.loc[working[col] == saturation_km, col] = np.nan

    mask = (
        (working["auto_count"] >= min_window_calls)
        & (working["range_D_MP1"] < max_range_km)
    )
    return working, mask.to_numpy()


def group_ranges(times, r1, range_jump_km=1.5, time_gap=ONE_HOUR):
    """Step 2: walk rows in order; new group on a range jump or a time gap.

    Returns 1-based group ids, one per row.
    """
    n = len(r1)
    groups = np.empty(n, dtype=int)
    if n == 0:
        return groups
    groups[0] = 1
    for j in range(1, n):
        new_group = (
            abs(r1[j] - r1[j - 1]) > range_jump_km
            or (times[j] - times[j - 1]) > time_gap
        )
        groups[j] = groups[j - 1] + 1 if new_group else groups[j - 1]
    return groups


def qualify_groups(groups, r1, window_calls, min_group_rows=12,
                   min_mean_calls=10.0, max_zero_fraction=0.5):
    """Step 3: per-row ``use_track`` flag.

    A group qualifies when it has at least ``min_group_rows`` rows, fewer than
    ``max_zero_fraction`` of its ``range_D_MP1`` values equal 0, and mean window
    call count strictly above ``min_mean_calls``.
    """
    use_track = np.zeros(len(groups), dtype=bool)
    for gid in np.unique(groups):
        idx = np.flatnonzero(groups == gid)
        zeros = np.count_nonzero(r1[idx] == 0)
        if (
            len(idx) >= min_group_rows
            and zeros < max_zero_fraction * len(idx)
            and np.mean(window_calls[idx]) > min_mean_calls
        ):
            use_track[idx] = True
    return use_track


def _segment_bounds(start_times, end_times, supertrack_gap, max_segment_groups):
    """Step 4: 1-based segment boundary indices.

    Splits between consecutive qualifying groups whose gap (next start minus
    previous end) exceeds ``supertrack_gap``; then splits any segment longer
    than ``max_segment_groups`` at its midpoint (halves rounded away from zero).
    """
    k = len(start_times)
    gapinds = [1]
    for g in range(k - 1):  # 1-based diff index g+1
        if abs(start_times[g + 1] - end_times[g]) > supertrack_gap:
            gapinds.append(g + 1)
    gapinds.append(k)

    lengths = np.diff(gapinds)
    large = [p + 1 for p, length in enumerate(lengths) if length > max_segment_groups]
    a = 0
    for pos in large:  # 1-based position into the original gapinds
        idx = pos - 1 + a
        gapinds.insert(idx + 1, _round_half_up((gapinds[idx] + gapinds[idx + 1]) / 2))
        a += 1
    return gapinds


def _assign_segment(start_ranges, end_ranges, chunk_size=3**12):
    """Step 5 for one segment: enumerate 3^n combinations, return hypotheses.

    ``start_ranges`` / ``end_ranges`` are (n, 3) arrays indexed
    [group, hypothesis]. Returns a list of n hypothesis codes (1..3).

    The enumeration streams in chunks so long segments stay memory-safe: a
    17-group supertrack is 3^17 ~ 129 M combinations, which materialising the
    whole table would not survive, and the >18-group midpoint split alone does
    not prevent that (see KNOWN_ISSUES.md, "Hypothesis-selection — behavioural
    notes"). The argmin is exact: combinations run
    with the first group varying slowest, NaN costs are omitted, ties go to the
    first minimum, and all-NaN falls back to the first combination. The square
    root of the cost is skipped — it is monotonic, so the argmin is unchanged.
    """
    n = len(start_ranges)
    total = 3**n
    rows = np.arange(n)
    best_idx, best_cost = 0, np.nan
    for lo in range(0, total, chunk_size):
        idx = np.arange(lo, min(lo + chunk_size, total))
        # Enumeration order: the first group varies slowest (C order).
        combos = np.stack(np.unravel_index(idx, (3,) * n), axis=1)
        starts = start_ranges[rows[None, :], combos]
        ends = end_ranges[rows[None, :], combos]
        cost = np.sum((starts[:, 1:] - ends[:, :-1]) ** 2, axis=1)
        try:
            k = int(np.nanargmin(cost))
        except ValueError:  # all-NaN chunk
            continue
        # Strict < keeps the earliest global minimum.
        if np.isnan(best_cost) or cost[k] < best_cost:
            best_idx, best_cost = int(idx[k]), float(cost[k])
    combo = np.unravel_index(best_idx, (3,) * n)
    return [int(c) + 1 for c in combo]


def select_hypotheses(ranges_df, min_group_rows=12, min_mean_calls=10.0,
                      start=None, max_range_km=25.0, min_window_calls=1,
                      saturation_km=40.0, range_jump_km=1.5,
                      time_gap=ONE_HOUR, supertrack_gap=THREE_HOURS,
                      max_segment_groups=18):
    """Run the automated selection; return the table with 4 new columns.

    Defaults are the published fin parameters (Hilmo et al. 2025): ranges
    within 1.5 km / 1 h form groups; groups of >= 12 ranges less than 3 h
    apart link into tracks; ``min_group_rows=12``, ``min_mean_calls=10``.
    The Bryde's profile uses ``min_group_rows=7``, ``min_mean_calls=2`` and
    1.6 km / 2 h. Columns added:
    ``groupnum`` (1-based, NaN outside the filtered rows), ``use_track``,
    ``supertrack`` (the 1-based boundary index) and ``best_hypothesis``
    (1 = MP1-Direct, 2 = MP2-MP1, 3 = MP3-MP2; NaN for single-group
    supertracks and unassigned rows).
    """
    working, mask = filter_ranges(
        ranges_df, start=start, max_range_km=max_range_km,
        min_window_calls=min_window_calls, saturation_km=saturation_km,
    )
    working["groupnum"] = np.nan
    working["use_track"] = False
    working["supertrack"] = np.nan
    working["best_hypothesis"] = np.nan

    sel = working[mask]
    if sel.empty:
        return working

    times = sel["time"].to_numpy()
    r1 = sel["range_D_MP1"].to_numpy(dtype=float)
    r2 = sel["range_MP1_MP2"].to_numpy(dtype=float)
    r3 = sel["range_MP2_MP3"].to_numpy(dtype=float)
    calls = sel["auto_count"].to_numpy(dtype=float)

    groups = group_ranges(sel["time"].tolist(), r1,
                          range_jump_km=range_jump_km, time_gap=time_gap)
    use_track = qualify_groups(groups, r1, calls,
                               min_group_rows=min_group_rows,
                               min_mean_calls=min_mean_calls)

    working.loc[sel.index, "groupnum"] = groups
    working.loc[sel.index, "use_track"] = use_track

    cluster = np.unique(groups[use_track])  # qualifying group ids, ascending
    if len(cluster) == 0:
        return working

    # Per qualifying group: first/last row's time and ranges (NaN values are
    # kept here; they drop out of the cost comparison instead).
    first = {g: np.flatnonzero(groups == g)[0] for g in cluster}
    last = {g: np.flatnonzero(groups == g)[-1] for g in cluster}
    start_times = [times[first[g]] for g in cluster]
    end_times = [times[last[g]] for g in cluster]
    start_ranges = np.array(
        [[r1[first[g]], r2[first[g]], r3[first[g]]] for g in cluster]
    )
    end_ranges = np.array(
        [[r1[last[g]], r2[last[g]], r3[last[g]]] for g in cluster]
    )

    gapinds = _segment_bounds(start_times, end_times, supertrack_gap,
                              max_segment_groups)

    hypotheses, supertracks, positions = [], [], []
    for i in range(len(gapinds) - 1):
        lo, hi = gapinds[i], gapinds[i + 1]  # 1-based inclusive slice
        seg = list(range(lo, hi + 1))
        if i > 0:
            seg = seg[1:]  # boundary group belongs to the earlier segment
        if not seg:
            continue
        if len(seg) == 1:
            hyp = [np.nan]  # single group: no neighbour to score against
        else:
            rows = [p - 1 for p in seg]
            hyp = _assign_segment(start_ranges[rows], end_ranges[rows])
        hypotheses.extend(hyp)
        supertracks.extend([lo] * len(seg))
        positions.extend(seg)

    for pos, hyp, st in zip(positions, hypotheses, supertracks, strict=True):
        gid = cluster[pos - 1]
        rows = sel.index[groups == gid]
        working.loc[rows, "best_hypothesis"] = hyp
        working.loc[rows, "supertrack"] = st

    return working


def selected_range(grouped_df):
    """``true_range``: each ``use_track`` row's range under its hypothesis."""
    out = pd.Series(np.nan, index=grouped_df.index, name="true_range")
    for code, col in _HYPOTHESIS_RANGE.items():
        rows = (grouped_df["use_track"] == True) & (  # noqa: E712
            grouped_df["best_hypothesis"] == code
        )
        out[rows] = grouped_df.loc[rows, col]
    return out


def interpolate_call_ranges(grouped_df, calls_df, peak_col="peak_time"):
    """Step 7: per-call ranges.

    For each supertrack among the ``use_track`` rows, linearly interpolate the
    selected range (``true_range``) against time onto every detected call's
    ``peak_time`` inside the supertrack's time span, and onto the full
    per-window table. Returns ``(calls_out, grouped_out)``, each a copy with
    an ``interp_range`` column. Supertracks with fewer than two rows are
    skipped (interpolation needs two points).
    """
    grouped_out = grouped_df.copy()
    grouped_out["time"] = pd.to_datetime(grouped_out["time"])
    calls_out = calls_df.copy()
    calls_out[peak_col] = pd.to_datetime(calls_out[peak_col])
    grouped_out["interp_range"] = np.nan
    calls_out["interp_range"] = np.nan

    tracks = grouped_out[grouped_out["use_track"] == True]  # noqa: E712
    true_range = selected_range(tracks)

    for st in sorted(tracks["supertrack"].dropna().unique()):
        sub = tracks[tracks["supertrack"] == st]
        if len(sub) < 2:
            continue
        x = sub["time"].astype("int64").to_numpy(dtype=float)
        y = true_range[sub.index].to_numpy(dtype=float)
        t0, t1 = sub["time"].min(), sub["time"].max()

        c = (calls_out[peak_col] >= t0) & (calls_out[peak_col] <= t1)
        calls_out.loc[c, "interp_range"] = np.interp(
            calls_out.loc[c, peak_col].astype("int64").to_numpy(dtype=float), x, y
        )
        m = (grouped_out["time"] >= t0) & (grouped_out["time"] <= t1)
        grouped_out.loc[m, "interp_range"] = np.interp(
            grouped_out.loc[m, "time"].astype("int64").to_numpy(dtype=float), x, y
        )
    return calls_out, grouped_out
