---
description: "Task list for the publication-readiness refactor"
---

*AI-generated draft (Claude, Anthropic) — for review. All parameters and figures are derived from version-controlled scripts and data.*

# Tasks: Publication-readiness refactor of the Marianas multipath ranging case study

**Spec**: `specs/001-publication-refactor/spec.md`
**Plan**: `specs/001-publication-refactor/plan.md`
**Generated**: 2026-09-25 (back-filled: completed tasks marked `[x]`)

## Format

`- [ ] T### Description with file path or specific action` — QC tasks labeled.

---

## Phase 1: Python packaging (DONE)

- [x] T001 Create `pyproject.toml` + editable install; 5 `whaletracks-*` console scripts
- [x] T002 Clean library core (`common/`, `detection/`) — ruff-clean, canonical `whaletracks.*` imports, camelCase kept as aliases
- [x] T003 Convert 6 legacy scripts into config-driven CLIs (`cli/*.py`) with YAML configs
- [x] T004 Keep `manual_picking.py` separate from `detect_calls.py` (genuinely different filter math)
- [x] T005 [QC] Golden-master tests pin core numeric outputs; `test_plot_ranges.py` proves B01 BELLHOP ranges byte-identical to `Marianas_auto_B01_v2.csv`
- [x] T006 [QC] `ruff` clean; `pytest` green; all 5 CLIs `--help` OK

## Phase 2: Species-agnostic pipeline (DONE)

- [x] T007 Parameterize `run_detection` for fin OR Bryde's via YAML (`detect_fin.yaml`, `detect_brydes.yaml`)
- [x] T008 Add `ranges_fin.yaml`, `ranges_brydes.yaml`; standardize output names
- [x] T009 Reproduce the published fin method; drop the unpublished T-phase discriminator (documented in `KNOWN_ISSUES.md`)
- [x] T010 One shared station table `data/Station_info_Marianas.csv` (7 published OBS); reorganize `data/{fin_whale,brydes_whale,bellhop_arrival_models}`
- [x] T011 [QC] Bryde's B01 golden output still byte-identical; 22 tests green
- [x] T012 Remove hardcoded FDSN credentials → anonymous `Client('IRIS')`

## Phase 3: Fin-whale tutorial (IN PROGRESS — not signed off)

- [x] T013 Rewrite `tutorials/multipath_ranging.qmd` for fin whales; fix data paths to `data/{fin_whale,bellhop_arrival_models}`
- [x] T014 Add `references.bib` (Hilmo & Wilcock 2024, Hilmo et al. 2025, Porter BELLHOP) + inline citations + References section
- [x] T015 Correct multipath physics (MPn = n surface + n reflector reflections; refraction) and the ray-path figure
- [x] T016 Reframe BELLHOP as the ranging model (provenance only) and `basic_ranging` as the search-window helper
- [x] T017 Add "Assumptions and limitations"; drop the deprecated summed-spectrogram alternative
- [x] T018 [QC] `quarto render` runs all 11 cells; citations resolve (only book-only `@sec-distance_sampling` warns)
- [x] T018b Factor the timing→range step into `whaletracks/detection/range_estimation.py` (shared by the `plot_ranges` CLI and the tutorial); add a worked ranging section — `@sec-matching` runs it live and `@sec-results` plots the computed table
- [x] T018e Switch the tutorial worked example to **B20 (CORTADO_TEST dataset)**; add tz-safe `valid_start`/`valid_end` date bounds to the ranging (config + function) and exclude Feb 2013 onward (airgun survey) → 7140 ranges (Mar 2012–Jan 2013); lock with `tests/test_plot_ranges_fin.py` (B20 CORTADO_TEST)
- [x] T018c Colour-accessibility pass: add Okabe–Ito standard to constitution Figure Standards; recolour all tutorial figures; filter BELLHOP near-field artifacts from the delay curve (`KNOWN_ISSUES` #10)
- [x] T018d Fix calling-depth citation (Watkins et al. 1987 + Stimpert et al. 2015, not Hilmo & Wilcock 2024); redraw ray-path figure (whale below surface, OBS above sub-seafloor reflector); revise §1.3.1 to be forward-leading
- [ ] T019 **Further PI-directed tutorial revisions** (ongoing — PI reviewing section by section); re-render and get PI sign-off

## Phase 4: Spec Kit governance + hygiene (DONE this session)

- [x] T020 Reduce to one environment definition: remove `environment_1.yml` and `uv.lock`
- [x] T021 Relocate orphan `All_Brydes_verified.csv` → `data/brydes_whale/` (history preserved)
- [x] T022 Correct README species framing + stale station-table reference
- [x] T023 Retrofit `.specify/` + `memory/constitution.md` + `specs/001-publication-refactor/{spec,plan,research,tasks}.md`

## Phase 5: Remaining Python debt (PENDING)

- [x] T024 [QC] Ship fin autocorrelation intermediates so fin ranging is reproducible offline — **B19 done**: `Marianas_auto_B19_mp_v2.csv` shipped; `range_estimation.py` reproduces `Marianas_auto_B19_v2.csv` from it (regenerated from the shipped timings — the stale 38k-row output that included the Feb 2012 airgun period was replaced with the 6474-row Mar–Oct 2012 result per Hilmo et al. 2025); locked by `tests/test_plot_ranges_fin.py`. Other fin stations still need their autocorr intermediates.
- [ ] T025 Add a per-output provenance manifest (station/channel/time + config id) — Principle III
- [ ] T026 Review + merge branch `modernize-python-segment`; push
- [ ] T027 **PI action**: rotate the FDSN password exposed in upstream history

## Phase 6: Convert MATLAB process to Python (PENDING)

> Scope change (PI, 2026-09-25): the MATLAB segment is to be **ported to Python**,
> not preserved as MATLAB. Same preserve-exactly discipline applies to the
> *outputs*: the Python port must reproduce the MATLAB numeric results.

- [ ] T028 Inventory `MATLABCodes/`: entry points, inputs, outputs, and overlap with the existing Python pipeline
- [ ] T029 Capture MATLAB reference outputs to serve as golden-master targets for the port
- [ ] T030 Port the process to Python (fold into `whaletracks` where it overlaps; new modules/CLIs where it doesn't)
- [ ] T031 [QC] Confirm the Python port reproduces the MATLAB outputs; document any deliberate deviation in `KNOWN_ISSUES.md`
- [ ] T032 Document the ported workflow in README (retire or archive `MATLABCodes/`)

## Phase 7: R segment (PENDING)

- [ ] T033 Inventory `Brydes_DE.R` (density estimation); document inputs/outputs and package deps
- [ ] T034 Refactor (or port — decide with PI) under preserve-exactly discipline; choose a reproducible env
- [ ] T035 [QC] Confirm R outputs match legacy; document deviations

---

**Checkpoint (current):** Phases 1–2 complete; Phase 3 (fin tutorial) in progress
— rewritten and rendering, **but further PI-directed revisions pending, not yet
signed off**; Phase 4 (Spec Kit layer + hygiene) complete on branch
`modernize-python-segment`. Next: finish tutorial revisions (T019), Phase 5 debt,
then MATLAB→Python conversion (Phase 6), then R (Phase 7).
