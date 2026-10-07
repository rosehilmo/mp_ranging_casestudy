*AI-generated draft (Claude, Anthropic) — for review. All parameters and figures are derived from version-controlled scripts and data.*

# Specification: Port the semi-automated multipath hypothesis selection to Python

**Feature**: `002-hypothesis-selection`
**Status**: **Complete** (2026-10-05) — port, CLI, tests, and tutorial section
shipped and merged to `main`. The planned MATLAB golden-master was **dropped**
with `MATLABCodes/` in the Python-only trim; the port is verified by structural
tests against the Python implementation instead (documented gap — see Validation
Approach).
**Created**: 2026-09-29
**Depends on**: `001-publication-refactor` (the `whaletracks` package and its
raw ranging output are this feature's input)

## Objectives

Convert the **semi-automated multipath hypothesis selection** process
(Hilmo et al. 2025, ESR — the step that decides which timing hypothesis,
MP1−Direct / MP2−MP1 / MP3−MP2, is real for each group of ranges, and that
removes spurious ranges) from MATLAB to Python, under the same
preserve-exactly-outputs discipline as feature 001. Then teach it: a new
tutorial section directly after the current "Results: the raw ranging output"
(`#sec-results`) walks the selection on the B20 worked example.

Concretely:

1. Port the selection algorithm into `whaletracks` (new module, e.g.
   `detection/hypothesis_selection.py`, plus a config-driven CLI), reproducing
   the MATLAB numeric outputs on a reference input.
2. Golden-master test: MATLAB reference input/output pair pinned in
   `tests/`, byte- or tolerance-identical.
3. New tutorial section after `#sec-results`: run the ported selection on
   `ranges_b20` live, show the selected tracks vs the raw three-hypothesis
   cloud (the natural continuation of the current @fig-ranges discussion).
4. Classify and disposition the three existing `MATLABCodes/` scripts (all
   downstream consumers, none implement the selection — see below).

## Algorithm (confirmed against the MATLAB source, 2026-09-29)

Source: `MATLABCodes/clean_group_ranges.m` (fin) /
`clean_group_ranges_Brydes.m` (same algorithm; Bryde's thresholds; commented) /
`interpolate_for_call_ranges_marianas.m` (follow-on per-call interpolation).

1. **Filter** the raw ranging table: time > deployment start (2012-03-01);
   any range equal to the 40-km BELLHOP table edge → NaN (saturated); keep rows
   with window call count (`auto_count`, MATLAB `sum_calls`) ≥ 1 AND
   `range_D_MP1` < 25 km.
2. **Group**: walk the filtered rows in time order; start a new group when
   |Δ `range_D_MP1`| > **1.5 km** OR Δt > 1 h; else extend the current group
   (`groupnum`). *(The MATLAB source used 1.6 km; corrected to the published
   1.5 km — Hilmo et al. 2025, PI-directed 2026-09-29, KNOWN_ISSUES #7. The
   Bryde's config and the golden test keep the MATLAB 1.6 km.)*
3. **Qualify** (`use_track`): a group qualifies when it has **> 11 rows** (fin;
   Bryde's > 6), fewer than 50 % of its `range_D_MP1` values equal 0, and
   mean(`auto_count`) **> 10** (fin; Bryde's > 2).
4. **Supertracks**: order the qualifying groups; split where the gap between
   consecutive groups (next start − previous end) exceeds **3 h** (published
   value; the MATLAB source used 2 h — KNOWN_ISSUES #7, Bryde's/golden keep
   2 h); segments
   with **> 18 groups** are additionally split at their midpoint (guard on the
   3^n combination count). Boundary quirk (reproduce exactly): the boundary
   group belongs to the earlier segment; the junction across a boundary is not
   scored.
5. **Assign hypotheses**: per supertrack of n groups, enumerate all **3^n**
   combinations of {MP1−Direct, MP2−MP1, MP3−MP2}; cost =
   sqrt( Σ over consecutive-group junctions (start_{k+1} − end_k)² ), with each
   group's start/end range read under its candidate hypothesis; argmin (first
   minimum, matching MATLAB `min`/lexicographic `combinations` order) →
   `best_hypothesis` per group + `supertrack` id. Single-group supertracks get
   `best_hypothesis = NaN` (MATLAB behaviour — reproduce).
6. **Manual verification (stays human)**: interactive loop per group — accept
   (0), override hypothesis (1/2/3), or reject (9 → `use_track = false`); the
   corrected table is written as `{station}_grouped_ranges_corrected.csv`.
7. **Per-call interpolation** (follow-on script): for `use_track == 1` rows,
   `true_range` = the range under `best_hypothesis`; per supertrack, linearly
   interpolate `true_range` vs time onto each detected call's `peak_time`
   (and onto the per-minute table) → `interp_range` per call.
8. Spurious (non-whale) ranges — earthquake swarms, T-phases, ship noise —
   fail the qualification/track criteria and drop out.

Note: the MATLAB uses `combinations` (requires MATLAB ≥ R2023a) and reads
columns positionally (2–4 = ranges, 7 = `auto_amp`, 8 = `auto_count`), matching
the feature-001 `RANGE_COLUMNS` order.

## Data Description

### MATLAB golden reference — dropped (PI, 2026-10-05)

- ~~The MATLAB source~~ — supplied 2026-09-29 (`clean_group_ranges.m`,
  `clean_group_ranges_Brydes.m`, `interpolate_for_call_ranges_marianas.m`), used
  to confirm the algorithm line by line, then **removed with `MATLABCodes/`** in
  the Python-only trim (recoverable from tag `full-dataset-pre-cleanup`).
- ~~A golden reference output~~ — the planned MATLAB-vs-Python golden-master was
  **not produced and is no longer planned**: the repository is Python-only, so a
  MATLAB reference run is no longer part of its reproducibility story. (The run
  was also at risk of exhausting MATLAB's memory on B20's 17-group supertrack —
  3^17 combinations — which the Python port streams in chunks.) The port's
  fidelity to the MATLAB therefore rests on the line-by-line algorithm
  confirmation (T102) plus structural tests, **not** on a numeric comparison.
  This gap is recorded here (the user-facing `KNOWN_ISSUES.md` documents the
  Python implementation's behaviour on its own terms, with no MATLAB framing).

### Shipped in the repo

- Raw ranging output (feature 001): `Marianas_auto_B20_CORTADO_TEST_v2.csv` —
  the selection's input format (`time`, `range_D_MP1`, `range_MP1_MP2`,
  `range_MP2_MP3`, `auto_max`, `auto_snr`, `auto_amp`, `auto_count`, `n_calls`).
- Selection outputs shipped as demonstration artifacts:
  `B20_grouped_ranges_CORTADO_TEST.csv` (automated) and
  `..._corrected.csv` (analyst-corrected companion; see `KNOWN_ISSUES.md`,
  "Demonstration data provenance").
- `MATLABCodes/` inventory (2026-09-29) — **all four scripts removed 2026-10-05**
  as downstream of ranging and out of scope; none implemented the selection:
  - `MultipathSearch.m` — scatter plot of grouped ranges filtered on
    `use_track == 1` (downstream viewer; input CSV was not in the repo).
  - `make_station_histograms.m` — Bryde's per-station/per-month range
    histograms from `All_call_ranges_interp_Brydes.csv`.
  - `make_montly_density_fig_Brydes.m` — Bryde's monthly density + 95% CI
    figure (distance-sampling arithmetic; hardcoded `w`, `Pdet`, `cfd`;
    `n = []` placeholder marked "change").
  - `pathdef.m` — MATLAB path file, no science.

## Expected Outputs

- `whaletracks/detection/hypothesis_selection.py` (pure functions) + the
  `whaletracks-select` CLI, config-driven (YAML with the
  grouping/linking/assignment thresholds — Principle IV).
- ~~Golden-master test pinning the MATLAB reference output~~ — dropped
  (see Data Description); structural tests of the Python implementation instead.
- Tutorial section after `#sec-results` running the selection on B20 live,
  with colourblind-safe figures (constitution Figure Standards).
- `KNOWN_ISSUES.md` entries for the implementation's notable behaviours and for
  the provenance of the shipped demonstration tables.
- Disposition of the three plotting/density scripts — **retired** with
  `MATLABCodes/` on 2026-10-05; they are downstream of ranging, not part of the
  selection.

## Validation Approach

- **Structural tests** of the Python implementation (grouping walk,
  qualification thresholds, noise/out-of-scope exclusion, the single-group
  unassigned case, interpolation, config parse).
- ~~Golden-master against a MATLAB reference run~~ — **not performed**; the
  known verification gap for this feature (see Data Description).
- `MPLBACKEND=Agg python -m pytest -q` green; `ruff` clean; `quarto render`
  clean — before every commit.
- Tutorial section renders against shipped data offline.

## Completion Criteria

- [x] MATLAB selection source supplied by the PI (2026-09-29)
- [x] Algorithm parameters confirmed against the source (grouping distance,
      time proximity, track criteria, RMS assignment) and reconciled with the
      published values (1.5 km / 3 h — `KNOWN_ISSUES.md` #6)
- [x] Python port in `whaletracks` with config + CLI; ruff clean
- [~] ~~Golden-master test against a MATLAB reference output~~ — **dropped with
      `MATLABCodes/`** (PI, 2026-10-05); verification rests on the line-by-line
      algorithm confirmation plus structural tests
- [x] Tutorial section added after `#sec-results` (B20 worked example)
- [x] `MATLABCodes/` scripts dispositioned — retired in the Python-only trim
- [x] Specs/tasks/constitution kept in sync (Spec Kit discipline)

## Assumptions & Limitations

- The port reproduces the *automated* selection; the manual analyst
  verification (spectrogram inspection, accept/reject) remains a human step —
  the port must preserve the columns/flags that step consumes and produces.
- Where the MATLAB source and the paper disagreed on thresholds, the **published
  values win** for the fin production config (1.5 km grouping, < 3 h track
  linking — `KNOWN_ISSUES.md` #6); the Bryde's config keeps the MATLAB values.
- The tutorial addition is fin/B20. The shipped analyst-corrected table is a
  demonstration artifact derived from the published review decisions, not a
  fresh review of the CORTADO data (`KNOWN_ISSUES.md`, "Demonstration data
  provenance").

## Notes

Feature 001's Phase 6 (T028–T032, generic "convert MATLAB to Python") is
superseded by this spec, which narrows scope to the hypothesis-selection
process per PI direction (2026-09-29) after the inventory (T028) showed
`MATLABCodes/` contains only downstream plotting/density scripts. This
feature was developed on branch `modernize-python-segment` alongside 001
(deliberate deviation from branch-per-feature, matching how 001 was
retrofitted); that branch was merged to `main` and pushed on 2026-10-05, and
`MATLABCodes/` was removed in the same Python-only trim.
