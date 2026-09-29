*AI-generated draft (Claude, Anthropic) — for review. All parameters and figures are derived from version-controlled scripts and data.*

# Specification: Publication-readiness refactor of the Marianas multipath ranging case study

**Feature**: `001-publication-refactor`
**Status**: Python segment complete; MATLAB & R segments pending
**Created**: 2026-09-25 (back-filled from the in-progress refactor)

## Objectives

Transform cloned research code (`mp_ranging_casestudy`) into reproducible,
installable, config-driven, documented, and tested form **without changing the
scientific results**, one language segment at a time (Python → MATLAB → R). The
outcome is code and a teaching tutorial that other researchers can clone, run,
and adapt.

Concretely:

1. Repackage the Python scripts into an **installable `whaletracks` package**
   with config-driven command-line entry points.
2. Make the detection/ranging pipeline **species-agnostic** (fin *and* Bryde's)
   through YAML profiles, reproducing the **published fin-whale method**.
3. Ship a **golden-master test suite** proving the refactor preserves legacy
   numeric outputs exactly.
4. Provide a **Quarto tutorial** teaching the fin-whale multipath method in the
   lab's documentation house style.
5. **Convert the MATLAB process to Python** (port reproducing MATLAB outputs),
   then refactor the **R** segment under the same discipline.

## Data Description

### Primary Data

- **Station table** — `data/Station_info_Marianas.csv`: 7 published good-data OBS
  (B19, B01, B02, B09, B12, B18, B20); instrument depth, sub-seafloor reflector
  depth, `HHZ` channel, per-station deployment dates.
- **BELLHOP arrival tables** — `data/bellhop_arrival_models/Marianas_ray_{station}_bellhop_arrivals.csv`:
  ray-traced direct + MP1/MP2/MP3 travel times vs range (0–40 km). Source of the
  **final ranges**.
- **Detection / range CSVs** — `data/{fin_whale,brydes_whale}/`: shipped
  detections (`{station}_mp.csv`), autocorrelation intermediates, and range
  outputs (`Marianas_auto_{station}_v2.csv`), plus Bryde's long-call year picks
  and `All_Brydes_verified.csv`. Fin autocorrelation intermediates are shipped
  for **B19** and **B20**; the tutorial's worked example uses the B20
  `*_CORTADO_TEST` files with `valid_end = 2013-02-01` excluding the Feb 2013+
  airgun survey (7105 ranged windows, Mar 2012 – Jan 2013, under the published
  ≥2/≥10 fin ranging gate).

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
   template (fin ≈22→15 Hz; Bryde's ≈37→33 Hz) yields a detection score.
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

Refactor discipline: **preserve outputs exactly**; flag suspected bugs in
`KNOWN_ISSUES.md`; keep conda; document any deliberate behavioural deviation.

## Expected Outputs

### Code / packages

- Installable `whaletracks` package (`pyproject.toml`, editable install) with 5
  `whaletracks-*` console scripts and a cleaned, ruff-clean, import-canonical
  library core, including the factored ranging module
  `detection/range_estimation.py` (`bellhop_timings`,
  `estimate_ranges_from_timings`).
- YAML configs: `detect_fin.yaml`, `detect_brydes.yaml`, `ranges_fin.yaml`,
  `ranges_brydes.yaml`, `verify_calls.yaml`, `manual_picker.yaml`.

### Tests

- Golden-master suite in `PythonCodes/tests/` (core numeric outputs; Bryde's B01
  BELLHOP-mode ranges byte-identical to `Marianas_auto_B01_v2.csv`; fin B20
  CORTADO_TEST ranges with the airgun `valid_end` bound locked by
  `test_plot_ranges_fin.py`); CLI config-parse and GUI import/`--help` smoke
  tests.

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
- Golden-master byte-identical checks for Bryde's B01 and fin B20 CORTADO_TEST
  ranges.
- `quarto render multipath_ranging.qmd` executes all cells against shipped data
  and resolves all citations (only the book-only `@sec-distance_sampling`
  cross-ref is expected to warn).
- Import-smoke + `--help` for GUI/network CLIs (cannot run headless).

## Completion Criteria

- [x] Python: installable package, 5 config-driven CLIs, golden-master tests
      green, ruff clean.
- [x] Species-agnostic pipeline (fin + Bryde's) via YAML; shared station table;
      Bryde's outputs preserved byte-identical.
- [~] Fin-whale Quarto tutorial rewritten, cited, and rendering clean —
      **further PI-directed revisions pending; not yet signed off.**
- [x] Environment reduced to a single deterministic definition
      (`environment.yml`); orphan CSV relocated under `data/`; README species
      framing corrected.
- [ ] MATLAB process **converted to Python** (port, not in-place refactor),
      reproducing the MATLAB numeric outputs.
- [ ] R segment (`Brydes_DE.R`) refactored (or ported — TBD with PI) under the
      same discipline.
- [ ] Per-output provenance manifest (station/channel/time + config id).
- [~] Fin autocorrelation intermediates shipped so fin `plot_ranges` is
      reproducible offline — **B20 (CORTADO_TEST) done and test-locked; the
      worked/tested fin station is B20 everywhere (PI, 2026-09-29). B19's
      intermediates remain shipped but are legacy (old ranging gate, untested);
      other fin stations pending.**
- [ ] FDSN password rotated by the PI (was hardcoded upstream).
- [ ] Branch `modernize-python-segment` reviewed and merged.

## Assumptions & Limitations

- Refactor, not re-analysis: results are inherited, not re-derived.
- Fin detection cannot be re-run offline here (needs IRIS + waveforms); shipped
  CSVs cover ranging and the tutorial.
- Method limitations are inherent (see tutorial): one singer at a time;
  inter-pulse interval must differ from multipath spacing; bathymetric relief and
  sedimented sites add uncertainty; usable range ~15 km single-station → 40 km
  pooled.
- MATLAB/R segments may require their native toolchains; "portable" is bounded by
  those runtimes.

## Notes

Back-filled to bring the repo under Spec Kit governance after the fact — the repo
was cloned, not scaffolded with `specify init`. Task history and decisions were
previously tracked only in session memory; `tasks.md` and `research.md`
materialize them. Related lab work: `sei_whale_atlantic`,
`goa_obs_transmission_loss`, `call_metrics`.
