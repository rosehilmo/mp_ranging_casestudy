*AI-generated draft (Claude, Anthropic) — for review. All findings reference version-controlled source; no algorithm behavior was changed.*

# Known issues — flagged, not fixed

During the publication-readiness refactor of `PythonCodes/`, the working rule
was **preserve outputs exactly**: structure and style were modernized, but
algorithm logic was left untouched. The items below are suspected correctness
bugs found while reading the legacy code. They are documented here for the
authors to decide on, rather than silently changed.

Line numbers refer to the original legacy scripts (before the CLI rewrite).

## 1. Detection pipeline — final write branch references a possibly-undefined name
`MP_Marianas_automation_Brydes.py`, end of `main()` (~L447–455):

```python
if len(analyzers) == 0:
    ...
elif len(analyzer_j.df) == 0:   # analyzer_j leaks from the inner loop
    ...                         # and this branch never writes final_analyzer_df
else:
    final_analyzer_df.to_csv(detection_pth, index=False)
```

`analyzer_j` is a loop-local from the per-station inner loop. It is only safe
because `len(analyzers) > 0` implies the loop ran, but the invariant is
implicit. In the `elif` branch no CSV is written even though detections may
exist. The rewrite (`whaletracks/cli/run_detection.py`) preserves this logic
and guards `analyzer_j` with an explicit `None` initializer.

## 2. Detection pipeline — inconsistent output path (global vs parameter)
Same file: the detection CSV is written to the `chunk_pth` **parameter** while
the autocorrelation CSV is written to `"auto_" + CHUNK_FILE`, a **module
global**. This only works because the top-level loop keeps the two equal. The
rewrite derives both paths consistently from `output_dir` + station, which is
behavior-identical when the legacy globals were equal.

## 3. Detection pipeline — possible IndexError on the final minute-chunk
Same file, multipath loop (~L343/L352):

```python
endind = one_minute * mp_iter + timescount
end_utc = utc_times[endind]      # endind can exceed len(utc_times)-1
```

On the last iteration `endind` can run past the end of `utc_times`, raising
`IndexError`. Not fixed; the rewrite preserves the same indexing.

## 4. Range plotting — analytic mode references an undefined variable
`plot_ranges_calltimings_autocorr_Brydes.py`: with `BELLHOP = False`, the range
loop uses `mp_3_timing`, which is only defined in the `BELLHOP == True` branch.
The analytic path therefore raised `NameError` and never worked. The active
configuration was `BELLHOP = True`.

In the rewrite (`whaletracks/cli/plot_ranges.py`), analytic mode fills
`mp_3_timing = t3 - t2` (consistent with the bellhop branch) and logs a warning.
This **enables** a path that previously crashed — results in analytic mode are
therefore new, not a reproduction of legacy output. The default mode is
`bellhop`, whose range output is verified byte-identical to the committed
`MarianasAutoFiles/Marianas_auto_B01_v2.csv` (see `tests/test_plot_ranges.py`).

## 5. Verification script — string used as a boolean
`brydes_call_verification.py` L33 (and `Brydes_manual_picker.py`):
`is_restart = 'True'` is a non-empty string, so it is **always truthy**
regardless of the intended value. The rewrite reads this as a real boolean
from the YAML config.

## 6. Interactive pick loops — off-by-one click ordering
`brydes_call_verification.py` and `Brydes_manual_picker.py`: the loops over the
clicked points do `for inds in range(0, len(clicks)): ind = inds - 1`, so they
start at index `-1` (the last click) and never reach index `len-1`. Every click
is still processed, but in a rotated order. Preserved exactly in the rewrites
(`whaletracks/cli/verify_calls.py`, `whaletracks/cli/manual_picker.py`).

## 7. Verification script — hardcoded column indices
`brydes_call_verification.py`: appended rows use hardcoded positional indices
(`new_row[5]`, `new_row[-3]`, `new_row[-1]`) that assume a fixed detection-CSV
schema and column count. Fragile if the schema changes. Preserved.

## 8. Interactive scripts — dead `PLOTFLAG = False` path
Both interactive scripts guard the plotting block behind `PLOTFLAG` but then use
the `ginput` results (`true_calls` / `Bry_calls`) unconditionally, so a
`PLOTFLAG = False` run would raise `NameError`. The default was `True`; the
rewrites make plotting unconditional (matching the only path that ever worked)
rather than preserve a broken branch.

## 9. Manual picker — records requested channel, not returned channel
`Brydes_manual_picker.py` stores the requested channel *string*
(`"HHZ,EHZ,ELZ,BHZ,EDH"`) in the CSV `channel` column instead of the channel
actually returned by the waveform request. Preserved.

