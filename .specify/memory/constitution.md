*AI-generated draft (Claude, Anthropic) — for review. All parameters and figures are derived from version-controlled scripts and data.*

# Marianas Multipath Whale Ranging — Refactor Constitution

## Research Context

This repository is a **publication-readiness refactor** of cloned research code
(`github.com/rosehilmo/mp_ranging_casestudy`) that detects **fin whale
(*Balaenoptera physalus*)** and **Bryde's whale (*Balaenoptera edeni*)** calls in
**ocean-bottom seismometer (OBS)** records from the **Marianas** region and
estimates whale-to-station **range** from the timing of **multipath acoustic
arrivals**. The fin-whale method is the published one of Hilmo & Wilcock (2024,
JASA) and Hilmo, Harris & Wilcock (2025, *Endangered Species Research*).

**Primary goal:** modernize the original scripts to **reproducible,
installable, config-driven, documented, and tested** form — one language segment
at a time — **without changing the scientific results.** The deliverable is code
and teaching material other researchers can clone, run, and adapt.

**Scope decision — refactor, not re-analysis.** This is an engineering effort,
not a new scientific study. Numeric outputs are **preserved exactly**; the
existing case-study results stand. Rigor concentrates on reproducibility,
provenance, and correctness of the *port*; new science (new stations, retuned
detectors, new density estimates) is explicitly out of scope.

**Segments, in order.** (1) **Python** — repackage into an installable
`whaletracks` package + Quarto tutorial (package done; tutorial in progress). (2)
**MATLAB → Python** (`MATLABCodes/`) — **convert** the MATLAB process to Python,
not preserve it as MATLAB (PI decision, 2026-09-25); the port must reproduce the
MATLAB outputs. (3) **R** (`Brydes_DE.R`) — refactor or port, TBD. Each segment
is handled under the same preserve-exactly (of outputs) discipline before the
next begins.

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

### VII. Behaviour-Preserving Refactor (project-specific)

The refactor **must not change algorithm logic or numeric outputs.** Suspected
correctness bugs are **documented in `KNOWN_ISSUES.md`, never silently fixed.**
**Golden-master tests** pin the numeric outputs of the library core (captured
from the legacy code); `test_plot_ranges.py` proves BELLHOP-mode ranges match
the committed `Marianas_auto_B01_v2.csv` byte-for-byte. Any intended behavioural
change (e.g. dropping the unpublished T-phase discriminator, fin-vs-Bryde's
threshold variations) is documented as a deliberate, reviewed deviation.

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
- **Detection / verified-call CSVs**: shipped per species under
  `data/{fin_whale,brydes_whale}/` (`{station}_mp.csv`, autocorrelation
  intermediates, `Marianas_auto_{station}_v2.csv` range outputs, Bryde's
  long-call year picks and `All_Brydes_verified.csv`).
- **Source — whale calls**: **fin** 20-Hz call, detected with a synthetic
  down-swept template ≈22→15 Hz over ~0.8 s (kernel in `detect_fin.yaml`);
  **Bryde's** ~37→33 Hz variant (`detect_brydes.yaml`). Multipath spacing is
  measured by **autocorrelation of the detection score** over a ~20-min window.
- **Literature**: Hilmo & Wilcock (2024, JASA, doi:10.1121/10.0024615) —
  **standard ASA copyright**; Hilmo, Harris & Wilcock (2025, ESR,
  doi:10.3354/esr01439) — **CC-BY 4.0**. `PythonCodes/literature/` is
  **gitignored** (do not commit the copyright PDF); cite the papers instead.

## Technical Environment

- Language: **Python 3.12** — the primary segment and the target for the MATLAB
  conversion (the process moves off MATLAB entirely). The **R** segment stays R
  unless a port is later agreed.
- Environment management: **conda** — `PythonCodes/environment.yml` (env
  `mp_ranging_casestudy`), with an editable install of the local `whaletracks`
  package via `pip: -e .`. **This is a deliberate deviation from the lab-default
  `uv`**: the upstream project is conda-based and the refactor preserves that to
  minimize migration risk (locked decision). To keep **one** deterministic path,
  the stale `environment_1.yml` and an unused `uv.lock` were removed.
- Key packages: **obspy** (FDSN + signal processing), numpy, scipy, pandas,
  matplotlib (publication), plotly (exploratory/tutorial), pyyaml, quarto +
  jupyter (tutorial render); dev: pytest, ruff.
- Console entry points (5): `whaletracks-detect`, `whaletracks-plot-ranges`,
  `whaletracks-histogram`, `whaletracks-verify`, `whaletracks-pick`. Run from
  `PythonCodes/` so config-relative data paths resolve.
- Compute: JupyterHub container on this host (CPU-capped ~32 cores; parallel jobs
  **≤ 24 workers** per lab policy). GUI/network CLIs require a display + IRIS
  access and are not run headless.
- Version control: git. Working branch `modernize-python-segment` (not yet
  merged/pushed). `Sample documentation_NEAREST/`, `literature/`, and Quarto
  render artifacts are gitignored.

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
  hover/zoom).
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
  values captured from the legacy code; B01 BELLHOP-mode ranges byte-identical to
  `Marianas_auto_B01_v2.csv`.
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
- **Deliverables:** (1) installable `whaletracks` Python package + golden-master
  tests; (2) fin-whale Quarto tutorial matching the `Sample
  documentation_NEAREST/` house style; (3) refactored MATLAB and R segments.
- **Ethical standard:** run the lab's `ethical-check` before introducing new
  literature/data, producing human-facing prose, regenerating a
  published-looking figure, or sharing outputs externally. Method parameters and
  citations come from the version-controlled code and the papers, not from
  memory.
