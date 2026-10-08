*AI-generated draft (Claude, Anthropic) — for review. All parameters and figures are derived from version-controlled scripts and data.*

# Plan: Publication-readiness refactor of the Marianas multipath ranging case study

**Spec**: `specs/001-publication-refactor/spec.md`
**Created**: 2026-09-25
**Status**: Python segment complete and merged to `main`; repository trimmed to a
Python-only B20 demonstration (2026-10-05); MATLAB & R out of scope

## Summary

Refactor cloned research code into an installable, config-driven, tested, and
documented form **without changing numeric outputs**. Approach: repackage Python
into `whaletracks` with YAML-driven CLIs and a golden-master safety net; make
detection/ranging species-agnostic (fin + Bryde's); implement the whole ranging
process in Python through hypothesis selection and per-call interpolation
(feature 002); write a fin-whale Quarto tutorial; then trim the repository to the
single-station B20 demonstration it is meant to be. Key outputs: the installed
package + tests, the tutorial, and this Spec Kit governance layer.

## Analysis Environment

**Language/Version**: Python 3.12 (the only language in the repository since the
2026-10-05 trim).
**Key Packages**: obspy, numpy, scipy, pandas, matplotlib, plotly, pyyaml,
quarto + jupyter; dev: pytest, ruff.
**Environment File**: `PythonCodes/environment.yml` (conda env
`mp_ranging_casestudy`) — the **single** deterministic definition (deliberate
conda over lab-default uv; `environment_1.yml` and `uv.lock` removed).

## Compute Environment

**Where will this run?**
- [x] Laptop/desktop / [x] Shared server (JupyterHub container, CPU-capped ~32
  cores; parallel jobs ≤ 24 workers)

**Data scale**: small — shipped CSVs and BELLHOP tables are < ~50 MB; waveform
re-download (optional) is larger and cached outside git.

**Timeline pressure**: none fixed; the fin tutorial supports teaching/case-study
use.

**Known bottlenecks**: GUI/network CLIs need a display + IRIS access and cannot
run headless; the conda env is not persistent across containers and is recreated
with `conda env create -f environment.yml`.

## Constitution Check

- [x] Data sources match those defined in constitution (XF Marianas OBS, 7
      published stations, BELLHOP tables, shipped CSVs, cited literature)
- [x] Coordinate systems/units are consistent (UTC, Hz, range m/km, depth m
      positive-down, WGS84)
- [x] Figure standards will be followed (tutorial = Plotly rendered as static
      PNGs — recorded deviation, see constitution Figure Standards; publication =
      matplotlib; Okabe–Ito colourblind-safe palette; captions disclosed)
- [x] Quality checks are incorporated (golden-master, ruff, pytest, quarto
      render)

**Issues to resolve**:
- FDSN password rotation is a **PI action** outside the repo.
- Resolved: the per-output provenance manifest (Principle III) is implemented —
  `common/provenance.py` writes a `<output>.provenance.yaml` sidecar from
  `run_detection`, `plot_ranges` and `select_hypotheses`.
- Resolved by the 2026-10-05 trim: fin autocorrelation intermediates (B20
  `CORTADO_TEST` shipped and test-locked; it is the only station shipped, by
  design) and MATLAB/R runtime portability (no MATLAB or R left in the repo).

## Project Structure

```text
mp_ranging_casestudy/
├── .specify/                      # Spec Kit toolkit (templates, scripts, constitution)
├── specs/001-publication-refactor/{spec,plan,research,tasks}.md
├── specs/002-hypothesis-selection/{spec,plan,tasks}.md
└── PythonCodes/                   # the whole repository (Python-only, DONE)
    ├── whaletracks/               # installable package (common/ detection/ cli/ config/)
    ├── tests/                     # golden-master + structural + smoke tests
    ├── tutorials/                 # multipath_ranging.qmd + references.bib
    ├── data/                      # station table, bellhop tables, fin_whale/ (B20 CORTADO_TEST)
    ├── environment.yml, pyproject.toml, README.md, KNOWN_ISSUES.md
    └── literature/                # gitignored (copyright PDFs)
```

`MATLABCodes/` and the R density scripts were removed on 2026-10-05 (restore tag
`full-dataset-pre-cleanup`; history not purged).

**Structure notes**: unlike the template's `scripts/ + data/{raw,processed}`
analysis layout, this is a library + CLI package; "stages" are the pipeline
commands below, and data is organized by species rather than by processing tier.

## Data Pipeline

### Stage 1: Detection (`whaletracks-detect`)
- **Input**: FDSN waveforms (network `XF`), station table, `detect_{species}.yaml`
- **Processing**: spectrogram → kernel cross-correlation → detection score →
  event picking → autocorrelation of the score over a ~20-min window
- **Output**: `data/{species}_whale/{station}_mp.csv`, `auto_{station}_mp.csv`
- **Note**: `basic_ranging` sets the multipath search window here (not ranges)

### Stage 2: Ranging (`whaletracks-plot-ranges`)
- **Input**: autocorrelation CSVs + BELLHOP tables, `ranges_{species}.yaml`
- **Processing**: match each delay to the nearest BELLHOP range (MP1/MP2/MP3),
  via `detection/range_estimation.py` (pure functions shared with the tutorial);
  optional `valid_start`/`valid_end` bounds exclude corrupted periods (B20:
  `valid_end = 2013-02-01`, airgun survey)
- **Output**: `data/{species}_whale/Marianas_auto_{station}_v2.csv` + figures

### Stage 3: Hypothesis selection (`whaletracks-select`, feature 002)
- **Input**: the ranging table + detections, `select_{species}.yaml`
- **Processing**: filter → group into tracks → qualify → link into supertracks →
  assign one hypothesis per group by minimum junction cost; optional `--review`
  analyst loop; then interpolate the corrected track range onto every call
- **Output**: `{station}_grouped_ranges*.csv` and the per-call `interp_range`
  table — the pipeline's final product

### Stage 4: Summaries & labeling
- `whaletracks-histogram` (yearly detection histogram); `whaletracks-verify` /
  `whaletracks-pick` (interactive GUI labeling; require display + network)

### Stage 5: Teaching tutorial
- `tutorials/multipath_ranging.qmd` → `quarto render` → HTML with executable
  Plotly figures

## Script/Notebook Plan

| Module / command | Purpose | Inputs | Outputs |
|---|---|---|---|
| `cli/run_detection.py` (`whaletracks-detect`) | detect + autocorrelate | FDSN, station table, config | `{station}_mp.csv`, `auto_{station}_mp.csv` |
| `cli/plot_ranges.py` (`whaletracks-plot-ranges`) | delays → range | auto CSV + BELLHOP, config | `Marianas_auto_{station}_v2.csv`, figs |
| `cli/select_hypotheses.py` (`whaletracks-select`) | tracks + hypothesis choice + per-call interpolation | ranging table, detections, config | `{station}_grouped_ranges*.csv`, per-call `interp_range` |
| `cli/make_histogram.py` (`whaletracks-histogram`) | yearly histogram | detection CSV | PNG |
| `cli/verify_calls.py` / `manual_picker.py` | interactive labeling | FDSN + config | verified CSVs |
| `detection/range_estimation.py` | pure timing→range functions (`bellhop_timings`, `estimate_ranges_from_timings`) | auto CSV + BELLHOP tables | ranges DataFrame |
| `detection/hypothesis_selection.py` | pure grouping / qualification / supertrack / assignment / interpolation functions | ranges DataFrame | grouped + per-call DataFrames |
| `detection/{detect_calls,event_analyzer,basic_ranging_model,manual_picking}.py` | library core | — | — |
| `tutorials/multipath_ranging.qmd` | fin-whale teaching doc | shipped data | HTML |

## Dependencies

```text
run_detection ──► plot_ranges ──► select_hypotheses ──► per-call interp_range
       │                                     │
       │                                     └─► (tutorial figures)
       └─ basic_ranging (search window only)          histogram
```

**Parallel opportunities**: stations are independent — detection/ranging can run
per-station in parallel (≤ 24 workers). The demonstration ships one station, so
this matters only when adapting the pipeline to a fuller dataset.

## Open Questions

- [x] Ship fin autocorrelation intermediates (make fin ranging
      offline-reproducible) — done for B20 (CORTADO_TEST, test-locked); the
      demonstration ships one station by design.
- [x] ~~MATLAB → Python conversion~~ — the selection algorithm was ported under
      feature 002; the remaining MATLAB/R scripts were retired in the
      2026-10-05 trim rather than ported (PI decision).
- [x] Adopt a provenance manifest format — **sidecar YAML per output**
      (`<output>.provenance.yaml`), chosen over an in-CSV header or a central
      registry: it travels with the file, never alters the output's bytes, and
      stays readable without the package installed.

## Notes

Back-filled after the fact; the repo was cloned rather than scaffolded. Decisions
and their rationale are in `research.md`; the executed and pending task list is
in `tasks.md`.
