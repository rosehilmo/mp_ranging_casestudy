---
description: "Task list for the publication-readiness refactor"
---

*Author: Rose Hilmo. Drafted with AI assistance (Claude, Anthropic), then edited and verified by the author. All parameters and figures are derived from version-controlled scripts and data.*

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
- [x] T005 [QC] Golden-master tests pin core numeric outputs; `test_plot_ranges.py` proves B01 BELLHOP ranges byte-identical to `Marianas_auto_B01_v2.csv` *(that Bryde's test was retired with its data in the 2026-10-05 trim — see T037)*
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
- [x] T018e Switch the tutorial worked example to **B20 (CORTADO_TEST dataset)**; add tz-safe `valid_start`/`valid_end` date bounds to the ranging (config + function) and exclude Feb 2013 onward (airgun survey) → ranges Mar 2012–Jan 2013; lock with `tests/test_plot_ranges_fin.py` (B20 CORTADO_TEST)
- [x] T018f Apply the published fin ranging gate (Hilmo et al. 2025: centre minute ≥2 calls AND 20-min window ≥10) in the offline timing→range step — configurable `min_center`/`min_window`/`window_length_s` in `estimate_ranges_from_timings` + `ranging:` block in `ranges_fin.yaml`; B20 CORTADO_TEST output regenerated (7140 → 7105 rows); Bryde's offline gate unchanged (B01 golden intact); tutorial §1.6/§1.7 prose updated (PI direction, 2026-09-29)
- [x] T018c Colour-accessibility pass: add Okabe–Ito standard to constitution Figure Standards; recolour all tutorial figures; filter BELLHOP near-field artifacts from the delay curve (`KNOWN_ISSUES` #10)
- [x] T018d Fix calling-depth citation (Watkins et al. 1987 + Stimpert et al. 2015, not Hilmo & Wilcock 2024); redraw ray-path figure (whale below surface, OBS above sub-seafloor reflector); revise §1.3.1 to be forward-leading
- [ ] T019 **Further PI-directed tutorial revisions** (ongoing — PI reviewing section by section); re-render and get PI sign-off

## Phase 4: Spec Kit governance + hygiene (DONE this session)

- [x] T020 Reduce to one environment definition: remove `environment_1.yml` and `uv.lock`
- [x] T021 Relocate orphan `All_Brydes_verified.csv` → `data/brydes_whale/` (history preserved)
- [x] T022 Correct README species framing + stale station-table reference
- [x] T023 Retrofit `.specify/` + `memory/constitution.md` + `specs/001-publication-refactor/{spec,plan,research,tasks}.md`

## Phase 5: Remaining Python debt (PENDING)

- [x] T024 [QC] Ship fin autocorrelation intermediates so fin ranging is reproducible offline — **B19 and B20 done**: B19 `Marianas_auto_B19_mp_v2.csv` shipped and `range_estimation.py` reproduces `Marianas_auto_B19_v2.csv` from it (regenerated from the shipped timings — the stale 38k-row output that included the Feb 2012 airgun period was replaced with the 6474-row Mar–Oct 2012 result per Hilmo et al. 2025); B20 CORTADO_TEST inputs + output shipped and locked by `tests/test_plot_ranges_fin.py` (with the `valid_end` airgun cut). Other fin stations still need their autocorr intermediates.
- [x] T024b **Decide the fate of the B19 fin outputs** — resolved by the PI's "use B20 everywhere, not B19" (2026-09-29): all configs, tests, examples and the 002 golden target now use B20 (CORTADO_TEST); the B19 files stay in the repo as shipped legacy data only (no test, no references). Removing them entirely remains open to the PI.
- [x] T025 Add a per-output provenance manifest (station/channel/time + config id) — Principle III. `whaletracks/common/provenance.py` writes a `<output>.provenance.yaml` sidecar recording the command + code version + git commit, the config file and its SHA-256 plus the parameters actually applied, the source network/station/channel/time span, and a SHA-256 + row count for every input. Wired into `run_detection` (where the waveform channel is authoritative), `plot_ranges` and `select_hypotheses`; the `--review` manifest is flagged as analyst-verified and not reproducible by re-running. Sidecars for the shipped B20 outputs were generated by re-running the pipeline (outputs byte-identical). 5 tests in `tests/test_provenance.py`
- [x] T026 Review + merge branch `modernize-python-segment`; push — merged to `main` and pushed (2026-10-05); `main` == `origin/main` == `python-only-demo` @ `1e89305`
- [ ] T027 **PI action**: rotate the FDSN password exposed in upstream history

## Phase 6: Convert MATLAB process to Python (→ feature 002; remainder retired)

> Scope change (PI, 2026-09-25): the MATLAB segment is to be **ported to Python**,
> not preserved as MATLAB. Same preserve-exactly discipline applies to the
> *outputs*: the Python port must reproduce the MATLAB numeric results.
>
> **Superseded (PI, 2026-09-29):** the port is scoped to the **semi-automated
> multipath hypothesis selection** (plus a tutorial section after
> `#sec-results`) and now runs as its own feature —
> `specs/002-hypothesis-selection/`. Key inventory finding (T028): the
> selection algorithm is NOT in `MATLABCodes/` (only downstream plotting /
> density scripts are).
>
> **Closed (PI, 2026-10-05):** `MATLABCodes/` was removed in the Python-only
> trim. The selection algorithm lives in Python (002); the remaining MATLAB
> scripts (two Bryde's figure scripts, one viewer, `pathdef.m`) were **retired,
> not ported** — all are downstream of ranging. Restore tag
> `full-dataset-pre-cleanup`.

- [x] T028 Inventory `MATLABCodes/`: entry points, inputs, outputs, and overlap with the existing Python pipeline — done 2026-09-29; findings recorded in `specs/002-hypothesis-selection/spec.md`
- [x] ~~T029–T032~~ moved to feature 002; the non-selection remainder retired with `MATLABCodes/` on 2026-10-05

## Phase 7: R segment (CLOSED — out of scope)

> **Closed (PI, 2026-10-05):** `Brydes_DE.R` and `DE_fin_calls.R` were removed in
> the Python-only trim. Density estimation is downstream of ranging and out of
> scope for this demonstration; the pipeline's final product is the per-call
> interpolated range table a density analysis would consume. Recoverable from
> tag `full-dataset-pre-cleanup`.

- [x] ~~T033–T035~~ closed, not performed — R segment removed from scope

## Phase 8: Python-only demonstration trim (DONE 2026-10-05)

- [x] T036 Branch + restore tag `full-dataset-pre-cleanup` before the destructive change; drive deletion from a dependency scan; verify with `pytest` + `quarto render` (PI-endorsed procedure)
- [x] T037 Remove `MATLABCodes/`, the R density scripts, all Bryde's data, and all non-B20 / full-deployment fin data; keep the BELLHOP tables, the shared station table, and the species-agnostic configs (adaptation examples); drop the Bryde's golden test and the MATLAB-reference golden from the selection tests — **29 tests green, tutorial renders clean** (`8beac0d`)
- [x] T038 Make the tutorial self-contained (no book-only cross-references — render is now warning-free); add Weirathmueller and Harris citations (`dab1b44`)
- [x] T039 Reframe `README.md`, `.specify/memory/constitution.md`, and `KNOWN_ISSUES.md` to the Python-only demonstration scope (`368191e`); document the provenance of the shipped B20 automated and analyst-corrected selection tables (`1e89305`)
- [x] T040 Sync `specs/001` and `specs/002` with the trim (this pass) — scope, data description, test inventory, completion criteria, and the closed MATLAB/R phases

---

**Checkpoint (current):** Phases 1–2, 4, 5 (except T025/T027) and 8 complete;
Phase 3 (fin tutorial) in progress — rendering warning-free, **but further
PI-directed revisions pending, not yet signed off**; Phases 6–7 closed (MATLAB
selection ported under feature 002, the rest retired with the Python-only trim).
All work is merged to `main` and pushed. Next: tutorial revisions (T019), then
the provenance manifest (T025); T027 is a PI action outside the repo.
