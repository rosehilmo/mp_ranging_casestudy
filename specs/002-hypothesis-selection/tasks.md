*AI-generated draft (Claude, Anthropic) — for review. All parameters and figures are derived from version-controlled scripts and data.*

# Tasks: Port the semi-automated multipath hypothesis selection to Python

**Spec**: `specs/002-hypothesis-selection/spec.md`

- [x] T101 Inventory `MATLABCodes/` (was 001/T028) — selection scripts supplied by PI 2026-09-29
- [x] T102 Confirm algorithm + thresholds against the MATLAB source (spec updated)
- [x] T103 Port `clean_group_ranges.m` → `whaletracks/detection/hypothesis_selection.py` (pure functions, MATLAB quirks preserved; enumeration streamed in chunks — MATLAB's in-memory 3^n table OOMs around n=14, see KNOWN_ISSUES "Hypothesis-selection port")
- [x] T104 Species configs `select_fin.yaml` / `select_brydes.yaml` + `whaletracks-select` CLI (6th console script; `--review` replays the MATLAB interactive verification, needs a display)
- [x] T105 Port `interpolate_for_call_ranges_marianas.m` → `interpolate_call_ranges()` (per-call `interp_range`; <2-row supertracks skipped — MATLAB would error)
- [x] T106 [QC] Synthetic structural tests (7) — grouping walk, qualification (fin vs Bryde's thresholds), noise/out-of-scope exclusion, single-group NaN quirk, interpolation, config parse; ruff clean; pytest green
- [ ] T107 [QC] Golden-master test vs the PI's MATLAB reference output (written, `skipif` until the file lands) — **PI action (B20 per 2026-09-29 direction): run `clean_group_ranges.m` (MATLAB ≥ R2023a) with `readtable` pointed at the repo's `Marianas_auto_B20_CORTADO_TEST_v2.csv`, line-354 `writetable` uncommented, and add `data/fin_whale/B20_grouped_ranges_CORTADO_TEST_matlab.csv`** (17-group supertrack may exhaust MATLAB memory — see spec caveat)
- [x] T111 Use B20 everywhere, not B19 (PI, 2026-09-29): golden target → B20; `ranges_fin.yaml` defaults → CORTADO_TEST templates + `valid_end` (fin test simplified accordingly); `select_fin.yaml` templates → CORTADO_TEST; example stations in CLIs/configs/tests → B20. B19 stays only as one of the 7 published OBS in the station table, in the shipped legacy data files, and in the factual near-field-artifact note (KNOWN_ISSUES #10 / delay-curve guard docstring).
- [x] T108 Tutorial: new `#sec-hypothesis_selection` after `#sec-results` — algorithm walkthrough, B20 run (7105 windows → 4791 rows / 108 groups / 28 supertracks; shipped intermediate `B20_grouped_ranges_CORTADO_TEST.csv` so renders stay fast), colourblind-safe cloud-vs-tracks figure, `--review` + per-call interpolation notes; code-map row added
- [x] T109 Sync docs: KNOWN_ISSUES port section, constitution console-script count 5→6, 001 tasks Phase 6 supersession
- [x] T112 Note in the tutorial that the automated first pass makes mistakes (obvious in the January track), corrected by analyst input; new `fig-corrected` comparing the MATLAB automated vs analyst-corrected selections (PI's `B20_grouped_ranges{,_corrected}.csv`, moved to `data/fin_whale/`) (PI, 2026-09-29)
- [x] T113 Verify grouping/track parameters against Hilmo et al. (2025) — paper says group within **1.5 km** / 1 h, link tracks with **< 3 h** gaps; MATLAB source had drifted to 1.6 km / 2 h. Fin config + library defaults corrected to the published values (KNOWN_ISSUES #7); Bryde's config and the golden test keep the MATLAB values; B20 shipped selection output regenerated (4767 track rows, 110 groups, 22 supertracks); mean-calls>10 and <50%-zeros criteria retained (not in paper, flagged) (PI, 2026-09-29)
- [ ] T110 Disposition of the remaining figure scripts (`make_station_histograms.m`, `make_montly_density_fig_Brydes.m`) — decide with PI
