*AI-generated draft (Claude, Anthropic) — for review. All parameters and figures are derived from version-controlled scripts and data.*

# Marianas Multipath Whale Ranging — Research Constitution

## Research Context

This repository provides a **Python implementation** of a method that detects
**fin whale (*Balaenoptera physalus*)** calls — and, via configuration, other
baleen-whale calls such as **Bryde's whale (*Balaenoptera edeni*)** — in
**ocean-bottom seismometer (OBS)** records from the **Marianas** region and
estimates whale-to-station **range** from the timing of **multipath acoustic
arrivals**. The method is the published one of Hilmo & Wilcock (2024, JASA) and
Hilmo, Harris & Wilcock (2025, *Endangered Species Research*), building on
Weirathmueller, Wilcock & Hilmo (2017, JASA).

**Primary goal:** a reproducible, installable, config-driven, documented, and
tested Python package (`whaletracks`) plus teaching material that other
researchers can clone, run, and **adapt to their own data**. A single-station
fin-whale **demonstration** (station B20) is shipped as the worked example.

**Scope decision — demonstration, not re-analysis.** This repository
demonstrates the ranging method end to end on one station; it is **not** a
reproduction of the published multi-station analysis, and the shipped B20
`CORTADO_TEST` data do **not** reproduce the paper's ranges or densities. Rigour
concentrates on reproducibility, provenance, correctness of the ranging
pipeline, and adaptability.

**Pipeline — Python only.** The entire ranging process — detection,
autocorrelation of the detection score, range estimation, semi-automated
hypothesis selection, and per-call interpolation — is implemented in Python
(`whaletracks`), with a Quarto tutorial. Density estimation is downstream of
ranging and **out of scope** here; the pipeline's final product is the per-call
interpolated range table that a density analysis would consume.

**Intended users:** The PI's own research group and readers of the case-study
tutorial (students and collaborators).

## Core Principles

### I. Reproducibility

Analysis is fully reproducible from shipped inputs to outputs. A run is described
by a **tracked YAML config**; commands run without manual intervention; any
randomness is seeded and documented (e.g. the tutorial's synthetic demo uses a
fixed `default_rng(1)`). There is **one** environment definition
(`PythonCodes/environment.yml`) and one package definition
(`PythonCodes/pyproject.toml`) — no competing lockfiles.

### II. Data Integrity

Shipped inputs (station table, BELLHOP tables, detection/verified-call CSVs) are
treated as immutable; transformations write **new** files, never overwrite
sources. Data lineage is traceable through the pipeline. Gaps and suspect
segments are flagged, not silently dropped or filled.

### III. Provenance

Every output links back to the code, the input data
(network/station/channel/time), and the parameter choices that produced it.
Output file names encode the station (`{station}_mp.csv`,
`auto_{station}_mp.csv`, `Marianas_auto_{station}_v2.csv`). If a range estimate
can't be traced to a waveform span and a config, it doesn't belong in the
results.

### IV. Configuration Is Versioned

Every detection and ranging run is defined by a tracked config recording:
stations/channels, time span, frequency band(s), preprocessing, detection kernel
and thresholds, autocorrelation window, ranging call-count criteria, and output
templates. Results are keyed to their config so any run can be regenerated. No
run parameter is hardcoded in the source.

### V. AI-Generated Text Is Disclosed

Prose drafted with AI assistance (README sections, tutorial prose and captions,
methods text, these Spec Kit documents) carries the lab's disclosure label and
is reviewed before use.

### VI. Portable & User-Editable

The repo clones and runs on a new machine from a short documented sequence
(`conda env create -f environment.yml` → `conda activate mp_ranging_casestudy` →
`whaletracks-*`). Tunable parameters live in labelled YAML — never buried as
magic numbers. READMEs document each command's purpose, inputs, outputs, and
editable parameters.

### VII. Verified, Documented Behaviour (project-specific)

**Golden-master tests** pin the numeric outputs of the library core against
captured reference values (`tests/golden/`); `test_plot_ranges_fin.py` locks the
BELLHOP-mode fin B20 (CORTADO_TEST) ranging output against the committed
`Marianas_auto_B20_CORTADO_TEST_v2.csv`. Known quirks and deliberate design
choices (e.g. the published ranging gate, the omission of an unpublished
T-phase discriminator) are **documented in `KNOWN_ISSUES.md`**, not left
implicit.

## Data Sources

<!-- For each source: name, access method, coverage, known issues. -->

- **Seismic waveforms & station metadata**: public **FDSN** (IRIS/EarthScope),
  network **`XF`** (Marianas), accessed via **ObsPy** with **anonymous** access
  (public data). *Security note:* upstream code contained hardcoded FDSN
  credentials; these were removed in the refactor — **the exposed password must
  still be rotated by the PI.**
- **Station set**: one shared table `PythonCodes/data/Station_info_Marianas.csv`
  = the **7 published good-data OBS** (B19, B01, B02, B09, B12, B18, B20), with
  per-station instrument depth, sub-seafloor reflector depth, channel (`HHZ`),
  and deployment dates (Feb 2012 → Jan/Feb 2013). Extra fin stations
  (B05/B06/B11/B14/N11/S10) present in some raw files are **not** in the
  published set and are excluded.
- **BELLHOP arrival tables**: per-station ray-traced travel-time tables in
  `PythonCodes/data/bellhop_arrival_models/` (`interp_r/d/mp1/mp2/mp3`, 0–40 km),
  provided with the repo, computed for the site profiles/geometry of Hilmo &
  Wilcock (2024). **These produce the final ranges.**
- **Detection / range CSVs**: the shipped demonstration set is for fin station
  **B20** under `data/fin_whale/` — `B20_mp_CORTADO_TEST.csv` (detections),
  `auto_B20_mp_CORTADO_TEST.csv` (autocorrelation),
  `Marianas_auto_B20_CORTADO_TEST_v2.csv` (ranges), and the grouped +
  analyst-corrected track tables. The Bryde's configs are retained as an
  adaptation example; Bryde's data is not shipped.
- **Source — whale calls**: **fin** 20-Hz call, detected with a synthetic
  down-swept template ≈22→15 Hz over ~0.8 s (kernel in `detect_fin.yaml`);
  **Bryde's** ~37→33 Hz variant (`detect_brydes.yaml`). Multipath spacing is
  measured by **autocorrelation of the detection score** over a ~20-min window.
- **Literature**: Hilmo & Wilcock (2024, JASA, doi:10.1121/10.0024615) —
  **standard ASA copyright**; Hilmo, Harris & Wilcock (2025, ESR,
  doi:10.3354/esr01439) — **CC-BY 4.0**. `PythonCodes/literature/` is
  **gitignored** (do not commit the copyright PDF); cite the papers instead.

## Technical Environment

- Language: **Python 3.12** — the entire ranging pipeline.
- Environment management: **conda** — `PythonCodes/environment.yml` (env
  `mp_ranging_casestudy`), with an editable install of the local `whaletracks`
  package via `pip: -e .`. **This is a deliberate deviation from the lab-default
  `uv`**: the upstream project is conda-based and the refactor preserves that to
  minimize migration risk (locked decision). To keep **one** deterministic path,
  the stale `environment_1.yml` and an unused `uv.lock` were removed.
- Key packages: **obspy** (FDSN + signal processing), numpy, scipy, pandas,
  matplotlib (publication), plotly (exploratory/tutorial), pyyaml, quarto +
  jupyter (tutorial render); dev: pytest, ruff.
- Console entry points (6): `whaletracks-detect`, `whaletracks-plot-ranges`,
  `whaletracks-histogram`, `whaletracks-verify`, `whaletracks-pick`,
  `whaletracks-select` (hypothesis selection, feature 002). Run from
  `PythonCodes/` so config-relative data paths resolve.
- Compute: JupyterHub container on this host (CPU-capped ~32 cores; parallel jobs
  **≤ 24 workers** per lab policy). GUI/network CLIs require a display + IRIS
  access and are not run headless.
- Version control: git. `Sample documentation_NEAREST/`, `literature/`, and
  Quarto render artifacts are gitignored.

## Coordinate Systems & Units

- Geographic CRS: **WGS84 (EPSG:4326)**, lon/lat decimal degrees.
- Time: **UTC**, ISO 8601 / ObsPy `UTCDateTime`.
- Frequency: Hz.
- Range / distance: metres internally, kilometres in figures.
- Depth: metres, **positive downward** (instrument depth, reflector depth).
- Missing data: `NaN` / ObsPy masked arrays; gaps flagged, never silently filled.

## Figure Standards

<!-- Per lab standards (CLAUDE.md). -->

- **Publication figures**: matplotlib, static, ≥ 300 DPI PNG or vector PDF.
- **Exploratory / student-facing (tutorial) figures**: Plotly (interactive
  hover/zoom). *Recorded deviation (PI decision, 2026-09-26):* the
  `multipath_ranging` tutorial renders its Plotly figures as **static PNGs**
  (kaleido, 2× scale) because the JupyterLab file preview sandboxes JavaScript —
  interactive divs never paint and leave layout gaps there.
- **Image display in notebooks**: matplotlib `imshow`.
- **Colour accessibility**: all figures must be colourblind-safe. Categorical /
  line series use the Okabe–Ito qualitative palette (avoid red–green pairings),
  and colour is never the *only* distinguishing channel — also vary line style
  (solid/dash/dot), marker, or direct labels so the figure reads in greyscale.
- Continuous / sequential data (spectrograms, scatter colour scales) use a
  perceptually uniform colormap (e.g. viridis); colorbar labelled with units;
  time in UTC, frequency in Hz.
- AI-drafted captions/markdown carry the disclosure label (tutorial uses the YAML
  metadata + header-callout form).

## Quality Checks

- **Golden-master**: numeric outputs of the library core re-checked against
  captured reference values; fin B20 (CORTADO_TEST) BELLHOP-mode ranges locked
  to `Marianas_auto_B20_CORTADO_TEST_v2.csv`.
- **Lint / tests**: `ruff` clean; `MPLBACKEND=Agg python -m pytest -q` green
  before any commit (lab rule). GUI/network CLIs covered by import / `--help` /
  config-parse smoke tests only.
- **Tutorial**: `quarto render` runs all cells against shipped data; citations
  resolve; only the book-only `@sec-distance_sampling` cross-ref is unresolved by
  design.
- **Band sanity**: detector band lies within the instrument passband; fin S.
  Atlantic-style high-frequency calls are out of band by design (fin target here
  is the 20-Hz pulse).
- Suspect data flagged in outputs, never silently patched.

## Project Notes

- **Collaborators / data-sharing:** internal to the PI's group. Waveforms are
  public FDSN; confirm data-center acknowledgement requirements before external
  sharing. Do not publish the whale-call ROC / embargoed products from sibling
  projects here.
- **Deliverables:** (1) installable `whaletracks` Python package + tests;
  (2) fin-whale Quarto tutorial (B20 demonstration) matching the `Sample
  documentation_NEAREST/` house style.
- **Ethical standard:** run the lab's `ethical-check` before introducing new
  literature/data, producing human-facing prose, regenerating a
  published-looking figure, or sharing outputs externally. Method parameters and
  citations come from the version-controlled code and the papers, not from
  memory.
