*AI-generated draft (Claude, Anthropic) — for review. All parameters and figures are derived from version-controlled scripts and data.*

# Specification: Port the semi-automated multipath hypothesis selection to Python

**Feature**: `002-hypothesis-selection`
**Status**: In progress — MATLAB source supplied 2026-09-29; **golden reference
outputs still needed** (see Data Description)
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

### Required from the PI (remaining blocker)

- ~~The MATLAB source~~ — **supplied 2026-09-29** (`clean_group_ranges.m`,
  `clean_group_ranges_Brydes.m`, `interpolate_for_call_ranges_marianas.m`).
- **A golden reference output** (PI decision 2026-09-29: **B20 everywhere,
  not B19**): the MATLAB scripts' `writetable` lines are commented out and no
  `*_grouped_ranges*.csv` is in the repo. For the golden-master test the PI
  should run `clean_group_ranges.m` once in MATLAB (≥ R2023a, for
  `combinations`) with its `readtable` pointed at the repo's
  `data/fin_whale/Marianas_auto_B20_CORTADO_TEST_v2.csv` and the line-354
  `writetable` uncommented, and provide the **automated** output (before the
  interactive loop) as
  `data/fin_whale/B20_grouped_ranges_CORTADO_TEST_matlab.csv`. The
  manually-corrected variant cannot serve as a deterministic golden. Caveat:
  the B20 data contains a 17-group supertrack (3^17 combinations) — MATLAB
  may exhaust memory there (see KNOWN_ISSUES); if so, a station/subset the
  MATLAB can complete is an acceptable golden and the PI should say which.

### Already in the repo

- Raw ranging output (feature 001): `Marianas_auto_{station}_v2.csv` /
  B20 CORTADO_TEST — the selection's input format (`time`, `range_D_MP1`,
  `range_MP1_MP2`, `range_MP2_MP3`, `auto_max`, `auto_snr`, `auto_amp`,
  `auto_count`, `n_calls`).
- `MATLABCodes/` inventory (2026-09-29):
  - `MultipathSearch.m` — scatter plot of grouped ranges filtered on
    `use_track == 1` (downstream viewer; input CSV not in repo).
  - `make_station_histograms.m` — Bryde's per-station/per-month range
    histograms from `All_call_ranges_interp_Brydes.csv` (present, 14 MB).
  - `make_montly_density_fig_Brydes.m` — Bryde's monthly density + 95% CI
    figure (distance-sampling arithmetic; hardcoded `w`, `Pdet`, `cfd`;
    `n = []` placeholder marked "change").
  - `pathdef.m` — MATLAB path file, no science; exclude from the port.

## Expected Outputs

- `whaletracks/detection/hypothesis_selection.py` (pure functions) + CLI
  (`whaletracks-select-hypotheses` or similar), config-driven (YAML with the
  grouping/linking/assignment thresholds — Principle IV).
- Golden-master test pinning the MATLAB reference output.
- Tutorial section after `#sec-results` running the selection on B20 live,
  with a colourblind-safe before/after figure (constitution Figure Standards).
- `KNOWN_ISSUES.md` entries for any deliberate deviation from the MATLAB.
- Disposition of the three plotting/density scripts (likely: port the two
  Bryde's figure scripts as small utilities or defer them to the R/density
  segment — decide with PI; they are *not* the selection algorithm).

## Validation Approach

- Golden-master: Python output matches the MATLAB reference output on the
  reference input (byte-identical where types allow; documented tolerance
  otherwise).
- `MPLBACKEND=Agg python -m pytest -q` green; `ruff` clean; `quarto render`
  clean — before every commit.
- Tutorial section renders against shipped data offline.

## Completion Criteria

- [ ] MATLAB selection source + reference input/output pair supplied by PI
- [ ] Algorithm parameters confirmed against the source (grouping distance,
      time proximity, track criteria, RMS assignment)
- [ ] Python port in `whaletracks` with config + CLI; ruff clean
- [ ] Golden-master test green against the MATLAB reference output
- [ ] Tutorial section added after `#sec-results` (B20 worked example)
- [ ] `MATLABCodes/` scripts dispositioned; dir archived or retired per plan
- [ ] Specs/tasks/constitution kept in sync (Spec Kit discipline)

## Assumptions & Limitations

- The port reproduces the *automated* selection; the manual analyst
  verification (spectrogram inspection, accept/reject) remains a human step —
  the port must preserve the columns/flags that step consumes and produces.
- Exact thresholds quoted in the paper (e.g. grouping distance, <12 ranges,
  >3 h) are taken from the MATLAB source, not from the paper text, wherever
  they differ.
- The tutorial addition is fin/B20; the Bryde's CSVs in `MATLABCodes/` serve
  the separate figure scripts, not the tutorial thread.

## Notes

Feature 001's Phase 6 (T028–T032, generic "convert MATLAB to Python") is
superseded by this spec, which narrows scope to the hypothesis-selection
process per PI direction (2026-09-29) after the inventory (T028) showed
`MATLABCodes/` contains only downstream plotting/density scripts. This
feature lives on branch `modernize-python-segment` alongside 001 (deliberate
deviation from branch-per-feature, matching how 001 was retrofitted; the
branch is still unmerged pending T026).
