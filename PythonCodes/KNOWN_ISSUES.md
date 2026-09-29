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

## 10. BELLHOP arrival tables — degenerate near-field rows (data, not code)
The provided ray tables in `data/bellhop_arrival_models/` (e.g.
`Marianas_ray_B19_bellhop_arrivals.csv`) have degenerate entries at very short
range where the higher multipaths are not well defined: for B19 the
`interp_mp3` time is spurious at range 0–10 m (e.g. −144 s and −17 s), and the
MP2−MP1 / MP3−MP2 spacings show scattered near-field spikes/dips out to ~230 m.
`interp_mp1 − interp_d` (MP1−Direct) is clean throughout. This does not affect
ranging — no whale is ranged that close, and within the critical range the
measured pair is MP1−Direct regardless — so the tables are left untouched
(preserve-exactly). The tutorial's delay-curve figure omits range < 0.3 km for
this reason; any future code that consumes these tables at sub-km range should
guard against the near-field rows.


## Species-agnostic unification (fin + Bryde's) — deliberate decisions

The detection pipeline (`whaletracks/cli/run_detection.py`) now ranges to fin
*or* Bryde's whales from a per-species config (`detect_fin.yaml` /
`detect_brydes.yaml`). Bryde's numeric behavior is unchanged (only output file
names were standardized to `{station}_mp.csv` / `auto_{station}_mp.csv`). The
fin profile reproduces the published method (Hilmo & Wilcock 2024; Hilmo et al.
2025) via `MP_Marianas_automation.py`, with these author-directed decisions:

1. **Earthquake/T-phase discriminator dropped.** The experimental
   `MultipathRanging_Fins.py` filtered ranging on a call-band vs low-band
   amplitude test (`db_amps + 5 > db_amps_eq`). This was *not* in the published
   method — Hilmo et al. (2025) reject earthquakes/T-phases by manual inspection
   and temporal track association, and explicitly name automated signal-based
   rejection as future work. It is therefore not implemented.

2. **Fin ranging thresholds set to the published values.** A range is attempted
   only when the center minute has ≥2 calls and the surrounding 20-min window has
   ≥10 calls (Hilmo et al. 2025), overriding this code copy's `≥1` / 10-min
   window. Bryde's keeps its own `≥1` center / `≥3` window. (The ≥12-range
   track-grouping is a separate downstream density-estimation step, not part of
   the ranging code.) **Extended 2026-09-29 (author decision):** the same ≥2/≥10
   gate is now also applied in the *offline* timing→range step
   (`range_estimation.estimate_ranges_from_timings`, via the `ranging:` block in
   `ranges_fin.yaml`), which previously required only ≥1 centre-minute call. The
   committed B20 CORTADO_TEST output was regenerated under this gate
   (7140 → 7105 rows). The offline Bryde's gate is unchanged (centre ≥1 only,
   defaults) — the B01 golden output is untouched. The committed
   `Marianas_auto_B19_v2.csv` still reflects the old ≥1 gate (its fate is an
   open author decision).

3. **Amplitude/SNR reference time made consistent.** The legacy fin script
   passed `utcstart_chunk` to the amplitude routine while passing
   `utcstart_chunk - 0.5*chunk_length` to the event picker — internally
   inconsistent. The unified code uses the `-0.5*chunk_length` reference for
   both, so amplitude/SNR align with the detections. This may shift fin
   amplitude/SNR values slightly versus the exact legacy script.

4. **Always-None frequency columns dropped.** The legacy fin output carried
   `peak_frequency`/`start_frequency`/… columns that were only populated for blue
   whales and always `None` for fin; they are no longer written.

5. **FDSN credentials removed.** `MP_Marianas_automation.py` contained a
   plaintext IRIS username/password; the pipeline now uses an anonymous
   `Client('IRIS')` (the data are public). That password should be rotated.

6. **Fin kernel start frequency corrected to the published value (author
   decision, 2026-09-29).** The `MP_Marianas_automation.py` copy used a 22→15 Hz
   template, but both papers state the Marianas fin template is **20→15 Hz over
   0.8 s** (Hilmo & Wilcock 2024, Table I; Hilmo et al. 2025). `detect_fin.yaml`
   now uses `f0: 20`. Note the shipped fin detection CSVs predate this config and
   were produced by the author's original runs. The SNR call band `[15.5, 21.5]`
   is retained as the automation code computed it (from the 22→15 kernel); a
   20-based recomputation would give `[14.5, 20.5]` — left for the author to
   decide before any detection re-run.

The fin detection path could not be executed here (needs IRIS access and a fin
station table, `Station_info_Marianas_fin.csv`, which is not distributed). It is
verified structurally (imports, config parse, `--help`); the author should
validate a fin run on real data.
