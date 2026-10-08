*Author: Rose Hilmo. Drafted with AI assistance (Claude, Anthropic), then edited and verified by the author. All parameters and figures are derived from version-controlled scripts and data.*

# Specification: Publication-readiness refactor of the Marianas multipath ranging case study

**Feature**: `001-publication-refactor`
**Status**: Python segment complete and merged to `main`; repository trimmed to a
Python-only B20 demonstration (2026-10-05) — the MATLAB and R segments are out of
scope
**Created**: 2026-09-25 (back-filled from the in-progress refactor)

## Objectives

Transform cloned research code (`mp_ranging_casestudy`) into reproducible,
installable, config-driven, documented, and tested form **without changing the
scientific results**. The outcome is code and a teaching tutorial that other
researchers can clone, run, and adapt.

Concretely:

1. Repackage the Python scripts into an **installable `whaletracks` package**
   with config-driven command-line entry points.
2. Make the detection/ranging pipeline **species-agnostic** (fin *and* Bryde's)
   through YAML profiles, reproducing the **published fin-whale method**.
3. Ship a **golden-master test suite** proving the refactor preserves legacy
   numeric outputs exactly.
4. Provide a **Quarto tutorial** teaching the fin-whale multipath method in the
   lab's documentation house style.
5. Implement the **whole ranging process in Python** — detection,
   autocorrelation, range estimation, semi-automated hypothesis selection
   (feature 002), and per-call interpolation.

**Scope change (PI, 2026-10-05) — Python-only demonstration.** The repository is
a single-station (B20 fin-whale) *demonstration* of the ranging method, not a
reproduction of the published multi-station analysis. `MATLABCodes/`, the R
density scripts, and all data beyond the B20 `CORTADO_TEST` demonstration set
were removed from the working tree (restore tag `full-dataset-pre-cleanup`; git
history deliberately not purged). Density estimation is downstream of ranging and
out of scope. The former objective "convert the MATLAB process to Python, then
refactor R" is superseded: the one MATLAB process that mattered — hypothesis
selection — was ported under feature 002, and the remaining MATLAB/R scripts were
retired rather than ported.

## Data Description

### Primary Data

- **Station table** — `data/Station_info_Marianas.csv`: 7 published good-data OBS
  (B19, B01, B02, B09, B12, B18, B20); instrument depth, sub-seafloor reflector
  depth, `HHZ` channel, per-station deployment dates.
- **BELLHOP arrival tables** — `data/bellhop_arrival_models/Marianas_ray_{station}_bellhop_arrivals.csv`:
  ray-traced direct + MP1/MP2/MP3 travel times vs range (0–40 km). Source of the
  **final ranges**.
- **Detection / range CSVs** — `data/fin_whale/`: the B20 `CORTADO_TEST`
  demonstration set only (detections `B20_mp_CORTADO_TEST.csv`, autocorrelation
  intermediate `auto_B20_mp_CORTADO_TEST.csv`, ranging output
  `Marianas_auto_B20_CORTADO_TEST_v2.csv`, and the automated and
  analyst-corrected hypothesis-selection tables
  `B20_grouped_ranges_CORTADO_TEST{,_corrected}.csv`). Ranging uses
  `valid_end = 2013-02-01` to exclude the Feb 2013+ airgun survey (7105 ranged
  windows, Mar 2012 – Jan 2013, under the published ≥2/≥10 fin ranging gate).
  These data **do not reproduce the published ranges or densities** — they exist
  to run the pipeline and tutorial end to end (see `KNOWN_ISSUES.md`,
  "Demonstration data provenance").
- **Removed 2026-10-05** (Python-only demonstration trim): all Bryde's data, all
  non-B20 / full-deployment fin data, and the B19 legacy outputs. The Bryde's
  *configs* (`detect_brydes.yaml`, `ranges_brydes.yaml`, `select_brydes.yaml`)
  are retained as worked adaptation examples for a second call type.

### Secondary Data

- **Seismic waveforms** — public FDSN (IRIS/EarthScope), network `XF`, anonymous
  access. Needed only to *re-run* detection; the shipped CSVs let ranging and the
  tutorial run **offline**.
- **Literature** — Hilmo & Wilcock (2024, JASA; ASA copyright) and Hilmo et al.
  (2025, ESR; CC-BY). PDFs kept local (`literature/`, gitignored); cited, not
  reproduced.

## Methods Overview

The multipath ranging method (see the tutorial and Hilmo & Wilcock 2024):

1. **Physics** — a near-surface whale call reaches a seafloor OBS along the
   direct path (D) plus multipaths MPn, each reflecting *n* times off the sea
   surface and *n* times off the sub-seafloor reflector. Water-column refraction
   bends rays away from the seafloor, so which paths reach the OBS depends on
   range.
2. **Detection** — 2-D spectrogram cross-correlation with a synthetic down-swept
   template (fin 20→15 Hz, 0.8 s, per Hilmo & Wilcock 2024 Table I; Bryde's
   ≈37→33 Hz) yields a detection score.
3. **Delay measurement** — autocorrelation of the detection score over a ~20-min
   window; peaks give the multipath delays.
4. **Ranging** — match each measured delay against the **BELLHOP** travel-time
   tables (nearest-point lookup), implemented in
   `whaletracks/detection/range_estimation.py` (shared by the `plot_ranges` CLI
   and the tutorial), with optional `valid_start`/`valid_end` date bounds to
   exclude corrupted periods (e.g. airgun surveys). Fin ranging uses the
   published gate (Hilmo et al. 2025): centre minute ≥ 2 detected calls AND
   ≥ 10 in the surrounding 20-min window; the offline Bryde's gate is the
   legacy centre ≥ 1. The analytic straight-ray model (`basic_ranging`) is used
   **only** to set the multipath search window, not for final ranges.
5. **Hypothesis selection and per-call interpolation** (feature 002) — group the
   ranged windows into tracks, choose one timing hypothesis per track by minimum
   junction cost, let an analyst correct the automated pass, then interpolate the
   corrected track range onto every detected call's `peak_time`. The resulting
   per-call range table is the pipeline's final product.

Refactor discipline: **preserve outputs exactly**; flag suspected bugs in
`KNOWN_ISSUES.md`; keep conda; document any deliberate behavioural deviation.

## Expected Outputs

### Code / packages

- Installable `whaletracks` package (`pyproject.toml`, editable install) with 6
  `whaletracks-*` console scripts and a cleaned, ruff-clean, import-canonical
  library core, including the factored ranging module
  `detection/range_estimation.py` (`bellhop_timings`,
  `estimate_ranges_from_timings`) and `detection/hypothesis_selection.py`
  (feature 002).
- YAML configs: `detect_fin.yaml`, `detect_brydes.yaml`, `ranges_fin.yaml`,
  `ranges_brydes.yaml`, `select_fin.yaml`, `select_brydes.yaml`,
  `verify_calls.yaml`, `manual_picker.yaml`.

### Tests

- Regression suite in `PythonCodes/tests/`: golden-master pins on the library
  core's numeric outputs (`test_golden_core.py`); fin B20 CORTADO_TEST ranges
  with the airgun `valid_end` bound locked by `test_plot_ranges_fin.py`;
  structural tests for the hypothesis-selection port; provenance-manifest tests;
  CLI config-parse and GUI import/`--help` smoke tests. **35 tests, all green.**
  The Bryde's B01
  BELLHOP-mode golden test was retired with the Bryde's data in the 2026-10-05
  trim (it is recoverable from tag `full-dataset-pre-cleanup`).

### Documentation

- `PythonCodes/README.md` (setup, layout, commands, testing, known issues).
- `PythonCodes/tutorials/multipath_ranging.qmd` — fin-whale Quarto tutorial
  (worked example: station B20, CORTADO_TEST dataset) with executable,
  colourblind-safe Plotly figures rendered as static PNGs (kaleido; deliberate
  deviation — see constitution Figure Standards), citations (`references.bib`),
  and the AI-disclosure label; renders clean via `quarto render`.
- `KNOWN_ISSUES.md` — suspected bugs, flagged not fixed.

## Validation Approach

- `MPLBACKEND=Agg python -m pytest -q` green; `ruff` clean — **before every
  commit** (lab rule).
- Golden-master byte-identical check for the fin B20 CORTADO_TEST ranges.
- `quarto render multipath_ranging.qmd` executes all cells against shipped data
  and resolves all citations and cross-references — **zero warnings** since the
  tutorial was made self-contained (2026-10-05).
- Import-smoke + `--help` for GUI/network CLIs (cannot run headless).

## Completion Criteria

- [x] Python: installable package, 6 config-driven CLIs, regression tests green,
      ruff clean.
- [x] Species-agnostic pipeline (fin + Bryde's) via YAML; shared station table.
      *(Bryde's byte-identical golden retired with its data in the 2026-10-05
      trim; recoverable from tag `full-dataset-pre-cleanup`.)*
- [~] Fin-whale Quarto tutorial rewritten, cited, and rendering clean (zero
      warnings) — **further PI-directed revisions pending; not yet signed off.**
- [x] Environment reduced to a single deterministic definition
      (`environment.yml`); orphan CSV relocated under `data/`; README species
      framing corrected.
- [x] Whole ranging process implemented in Python, through hypothesis selection
      and per-call interpolation (feature 002).
- [x] Repository trimmed to the Python-only B20 demonstration; restore tag
      `full-dataset-pre-cleanup` created; README/constitution/KNOWN_ISSUES
      reframed (PI, 2026-10-05).
- [~] ~~MATLAB process converted to Python~~ / ~~R segment refactored~~ —
      **out of scope** after the 2026-10-05 trim: the selection algorithm was
      ported (002) and the remaining MATLAB/R scripts were retired, not ported.
- [x] Per-output provenance manifest (station/channel/time + config id) —
      `<output>.provenance.yaml` sidecars written by `common/provenance.py`.
- [x] Fin autocorrelation intermediates shipped so fin ranging is reproducible
      offline — **B20 (CORTADO_TEST) shipped and test-locked**; it is the only
      station the demonstration ships, by design.
- [ ] FDSN password rotated by the PI (was hardcoded upstream).
- [x] Branch `modernize-python-segment` reviewed, merged to `main`, and pushed.

## Assumptions & Limitations

- Refactor, not re-analysis: results are inherited, not re-derived.
- **Demonstration, not reproduction**: the shipped B20 `CORTADO_TEST` data run
  the pipeline end to end but do not reproduce the published ranges or densities.
- Fin detection cannot be re-run offline here (needs IRIS + waveforms); shipped
  CSVs cover ranging, selection, and the tutorial.
- Method limitations are inherent (see tutorial): one singer at a time;
  inter-pulse interval must differ from multipath spacing; bathymetric relief and
  sedimented sites add uncertainty; usable range ~15 km single-station → 40 km
  pooled.
- Density estimation is downstream of ranging and out of scope; the pipeline's
  final product is the per-call interpolated range table a density analysis
  would consume.

## Notes

Back-filled to bring the repo under Spec Kit governance after the fact — the repo
was cloned, not scaffolded with `specify init`. Task history and decisions were
previously tracked only in session memory; `tasks.md` and `research.md`
materialize them. Related lab work: `sei_whale_atlantic`,
`goa_obs_transmission_loss`, `call_metrics`.
