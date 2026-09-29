*AI-generated draft (Claude, Anthropic) — for review. All parameters and figures are derived from version-controlled scripts and data.*

# Plan: Publication-readiness refactor of the Marianas multipath ranging case study

**Spec**: `specs/001-publication-refactor/spec.md`
**Created**: 2026-09-25
**Status**: Python segment complete; MATLAB & R pending

## Summary

Refactor cloned research code into an installable, config-driven, tested, and
documented form **without changing numeric outputs**, one language segment at a
time. Approach: repackage Python into `whaletracks` with YAML-driven CLIs and a
golden-master safety net; make detection/ranging species-agnostic (fin +
Bryde's); write a fin-whale Quarto tutorial; then port MATLAB and R. Key outputs:
the installed package + tests, the tutorial, and this Spec Kit governance layer.

## Analysis Environment

**Language/Version**: Python 3.12 (primary); MATLAB and R for their segments.
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
- Per-output provenance manifest (Principle III) not yet materialized — ranges
  are traceable via config + file names but no explicit manifest.
- Fin autocorrelation intermediates: **B20 (CORTADO_TEST) shipped and
  test-locked** — the worked/tested fin station everywhere (PI, 2026-09-29);
  B19's remain shipped as legacy only. Remaining fin stations still need theirs
  (or document the gap).
- FDSN password rotation is a **PI action** outside the repo.
- MATLAB/R portability bounded by native runtimes (Principle VI caveat).

## Project Structure

```text
mp_ranging_casestudy/
├── .specify/                      # Spec Kit toolkit (templates, scripts, constitution)
├── specs/001-publication-refactor/{spec,plan,research,tasks}.md
├── PythonCodes/                   # segment 1 (DONE)
│   ├── whaletracks/               # installable package (common/ detection/ cli/ config/)
│   ├── tests/                     # golden-master + smoke tests
│   ├── tutorials/                 # multipath_ranging.qmd + references.bib
│   ├── data/                      # station table, bellhop tables, {fin,brydes}_whale/
│   ├── environment.yml, pyproject.toml, README.md, KNOWN_ISSUES.md
│   └── literature/                # gitignored (copyright PDFs)
├── MATLABCodes/                   # segment 2 (PENDING — convert to Python, then archive)
└── Brydes_DE.R                    # segment 3 (PENDING)
```

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

### Stage 3: Summaries & labeling
- `whaletracks-histogram` (yearly detection histogram); `whaletracks-verify` /
  `whaletracks-pick` (interactive GUI labeling; require display + network)

### Stage 4: Teaching tutorial
- `tutorials/multipath_ranging.qmd` → `quarto render` → HTML with executable
  Plotly figures

## Script/Notebook Plan

| Module / command | Purpose | Inputs | Outputs |
|---|---|---|---|
| `cli/run_detection.py` (`whaletracks-detect`) | detect + autocorrelate | FDSN, station table, config | `{station}_mp.csv`, `auto_{station}_mp.csv` |
| `cli/plot_ranges.py` (`whaletracks-plot-ranges`) | delays → range | auto CSV + BELLHOP, config | `Marianas_auto_{station}_v2.csv`, figs |
| `cli/make_histogram.py` (`whaletracks-histogram`) | yearly histogram | detection CSV | PNG |
| `cli/verify_calls.py` / `manual_picker.py` | interactive labeling | FDSN + config | verified CSVs |
| `detection/range_estimation.py` | pure timing→range functions (`bellhop_timings`, `estimate_ranges_from_timings`) | auto CSV + BELLHOP tables | ranges DataFrame |
| `detection/{detect_calls,event_analyzer,basic_ranging_model,manual_picking}.py` | library core | — | — |
| `tutorials/multipath_ranging.qmd` | fin-whale teaching doc | shipped data | HTML |

## Dependencies

```text
run_detection ──► plot_ranges ──► (histogram / tutorial figures)
       │
       └─ basic_ranging (search window only)
```

**Parallel opportunities**: stations are independent — detection/ranging can run
per-station in parallel (≤ 24 workers). MATLAB and R segments are independent of
the Python segment.

## Open Questions

- [x] Ship fin autocorrelation intermediates (make fin `plot_ranges`
      offline-reproducible) — done for B20 (CORTADO_TEST, test-locked; the
      worked station everywhere per PI); remaining fin stations still open.
- [ ] MATLAB → Python conversion (PI decision): what does `MATLABCodes/` compute,
      how much overlaps the existing `whaletracks` pipeline, and what MATLAB
      reference outputs anchor the port's golden check?
- [ ] R segment (`Brydes_DE.R`): renv lockfile vs documented package list?
- [ ] Adopt a provenance manifest format (e.g. sidecar YAML per output)?

## Notes

Back-filled after the fact; the repo was cloned rather than scaffolded. Decisions
and their rationale are in `research.md`; the executed and pending task list is
in `tasks.md`.
