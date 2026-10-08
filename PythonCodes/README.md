*AI-generated draft (Claude, Anthropic) — for review. All parameters and figures are derived from version-controlled scripts and data.*

# whaletracks — multipath whale-call ranging (Marianas fin-whale demonstration)

Detect baleen-whale calls in ocean-bottom seismometer / hydrophone records and
estimate whale-to-station range from the timing of multipath acoustic arrivals.
This repository ships the **Python** implementation of the ranging method and a
worked, end-to-end **demonstration** on a single Gulf-of-Marianas fin-whale
station (**B20**).

`whaletracks` is a config-driven package — a shared library core, command-line
entry points, and YAML configuration files that hold every run parameter
(nothing is hardcoded in the source). It is written to be **general and
adaptable**: the same pipeline ranges to any call type for which you supply a
detection kernel and per-station travel-time tables (see *Adapting to your own
data* below). The fin profile follows the published method of Hilmo & Wilcock
(2024) and Hilmo et al. (2025).

> **Demonstration scope.** The shipped data are a `CORTADO_TEST` subset for
> station B20, provided to run the pipeline and tutorial end to end. They are
> **not** the published dataset and do not reproduce the paper's ranges or
> densities. Distance-sampling **density estimation** is downstream of ranging
> and out of scope here; it consumes the per-call interpolated ranges the
> ranging pipeline produces.

## Environment

```bash
conda env create -f environment.yml      # or: mamba env create -f environment.yml
conda activate mp_ranging_casestudy

# One-time, needed only to render the tutorial: fetch the Chromium that Plotly
# uses to export static figures.
kaleido_get_chrome
```

This installs the scientific stack (numpy, scipy, pandas, matplotlib, obspy),
`pyyaml`, Quarto, and dev tools (`pytest`, `ruff`), and performs an editable
install of the local `whaletracks` package (so the `whaletracks-*` commands
below are on your PATH).

Verify the install — this exercises the whole offline pipeline against the
shipped data:

```bash
MPLBACKEND=Agg python -m pytest -q       # expect: 35 passed
```

Run every command below from this `PythonCodes` directory: the configs use data
paths relative to it.

## Layout

```
whaletracks/
  common/      constants.py, util.py          # shared constants + conversions
  detection/   detect_calls.py                 # spectrogram / kernel / cross-correlation
               event_analyzer.py               # peak picking -> detection DataFrames
               basic_ranging_model.py          # analytic straight-ray helper (sets multipath search window)
               range_estimation.py             # timing -> range matching (shared with the tutorial)
               hypothesis_selection.py         # semi-automated multipath hypothesis selection
               manual_picking.py               # helpers for the manual picker (distinct math)
  cli/         run_detection.py                # automated detection + ranging
               plot_ranges.py                  # range estimation + plots
               select_hypotheses.py            # hypothesis selection + analyst review
               make_histogram.py               # yearly detection histogram
               verify_calls.py                 # interactive call verification (GUI)
               manual_picker.py                # interactive manual picking (GUI)
  config/      detect_fin.yaml, detect_brydes.yaml   # detection configs (per call type)
               ranges_fin.yaml, ranges_brydes.yaml   # range-estimation configs
               select_fin.yaml, select_brydes.yaml   # hypothesis-selection configs
               verify_calls.yaml, manual_picker.yaml
tests/         golden-master + regression tests
data/
  Station_info_Marianas.csv   station table (the 7 published good-data OBS)
  bellhop_arrival_models/     per-station BELLHOP ray-arrival tables (the forward model)
  fin_whale/                  B20 CORTADO_TEST demonstration set (detections,
                              autocorrelation, ranges, grouped + corrected tracks)
```

The `detect_brydes.yaml` / `ranges_brydes.yaml` / `select_brydes.yaml` configs
are retained as a **worked example of adapting the pipeline to a second call
type** — they differ from the fin configs only in parameters. The Bryde's
*data* is not shipped; point those configs at your own detections to use them.

## Commands

Each command takes `--config <yaml>` and writes CSVs / figures. Run from the
`PythonCodes` directory so the relative data paths in the configs resolve.

### Automated detection + multipath ranging
```bash
whaletracks-detect --config whaletracks/config/detect_fin.yaml --station B20
```
Downloads waveforms from IRIS, detects calls, measures SNR/amplitude, and
autocorrelates the detection score to time multipath arrivals. Per-station
geometry, channel, and dates come from the station-info CSV named in the
config. **Requires network access.**

### Range estimation + plots
```bash
whaletracks-plot-ranges --config whaletracks/config/ranges_fin.yaml \
    --station B20 --save ranges_B20.png
```
Matches each autocorrelation minute's strongest multipath timing to a
theoretical timing-vs-distance curve (BELLHOP ray table from
`data/bellhop_arrival_models/`, or the analytic model) and writes range
estimates to `data/fin_whale/`. Offline — runs on the shipped B20 CSVs.

### Multipath hypothesis selection (semi-automated)
```bash
whaletracks-select --config whaletracks/config/select_fin.yaml --station B20            # automated
whaletracks-select --config whaletracks/config/select_fin.yaml --station B20 --review   # + analyst loop (GUI)
```
Groups the raw ranges, links qualifying groups into whale tracks, and assigns
the best timing hypothesis (MP1−Direct / MP2−MP1 / MP3−MP2) per group by
minimising the mismatch between consecutive groups (the semi-automated step of
Hilmo et al. 2025). `--review` runs the interactive analyst verification
(accept / override / reject) and writes a `*_corrected.csv`. Offline; the
worked station is B20 (CORTADO_TEST dataset).

### Detection histogram
```bash
whaletracks-histogram --input data/fin_whale/B20_mp_CORTADO_TEST.csv \
    --threshold 150 --save hist_B20.png
```

### Tutorial

```bash
quarto render tutorials/multipath_ranging.qmd
```

Builds `tutorials/multipath_ranging.html` — a self-contained page (no network,
no CDN; figures embedded as static PNGs) that teaches the method and walks the
code, running the ranging and selection steps live against the shipped B20 data.
Open it in any browser. The render takes a few minutes, mostly in the
hypothesis-selection cell; it needs `kaleido_get_chrome` to have been run once.
A clean render emits no warnings.

**From R / RStudio.** `.qmd` is a Quarto format, not a Python one — RStudio and
Positron open, edit and render this file natively. But its sixteen code cells
are all `{python}` under a `jupyter: python3` engine (there is no R or `knitr`
code in it), so the render still runs on the conda environment above. Either
activate the environment before launching RStudio, or set
`QUARTO_PYTHON` to that environment's interpreter:

```bash
export QUARTO_PYTHON="$(conda run -n mp_ranging_casestudy which python)"
```

A `ModuleNotFoundError` on the first cell means Quarto picked up the wrong
Python. Reading the rendered HTML needs neither R nor Python.

### Interactive verification / manual picking (GUI + network)
```bash
whaletracks-verify --config whaletracks/config/verify_calls.yaml
whaletracks-pick   --config whaletracks/config/manual_picker.yaml
```
These open matplotlib windows and use `ginput` for click-based labeling; they
also fetch waveforms from IRIS. They cannot run headless.

## Adapting to your own data

The pipeline is call-type- and site-agnostic. To range a new dataset:

1. **Station table** — add your OBS to a station-info CSV (lon/lat, instrument
   depth, sub-seafloor reflector depth, channel, deployment dates) and point
   the config's `station_table` at it.
2. **Forward model** — supply a per-station BELLHOP ray-arrival table
   (`interp_r/d/mp1/mp2/mp3`) in `data/bellhop_arrival_models/`, computed for
   your site's sound-speed profile and geometry.
3. **Detection kernel** — set the `kernel` block (sweep `f0 → f1`, bandwidth,
   duration) and frequency bands for your call in a `detect_*.yaml`.
4. **Thresholds** — set the autocorrelation window and the ranging call-count
   gate (`ranging: min_center / min_window`) for your call rate.

Every run parameter lives in the YAML; the `fin` configs are the worked example
and the `brydes` configs show a second parameterisation.

## Testing

```bash
MPLBACKEND=Agg python -m pytest -q
```

The suite is a **golden-master safety net**: numeric outputs of the library
core are pinned against values captured from reference inputs
(`tests/golden/`, built by `tests/golden_inputs.py`), so refactors are provably
output-preserving. `test_plot_ranges_fin.py` locks the BELLHOP-mode ranging
output for fin B20 (CORTADO_TEST) against the committed
`data/fin_whale/Marianas_auto_B20_CORTADO_TEST_v2.csv`;
`test_hypothesis_selection.py` covers the grouping, qualification, supertrack
assignment, and per-call interpolation on synthetic data. GUI/network CLIs are
covered by import / `--help` / config-parse smoke tests only.

## Provenance sidecars

Every CSV the pipeline writes gets a companion manifest:

```
Marianas_auto_B20_CORTADO_TEST_v2.csv
Marianas_auto_B20_CORTADO_TEST_v2.csv.provenance.yaml
```

The sidecar records the command and code version that produced the file, the
config used (with a SHA-256, so a changed parameter is visible), the
network / station / channel / time span of the source data, and a SHA-256 and
row count for **every input** — so any result can be traced back to the exact
bytes and parameters behind it.

Manifests are descriptive: writing one never alters the output it describes.
Re-running a stage reproduces the same output bytes but a fresh timestamp, so a
manifest diff touching only `generated.utc` means the result reproduced cleanly.
The sidecars shipped with the demonstration data were generated this way.

## Known issues

Design notes and known quirks of the implementation are documented in
[`KNOWN_ISSUES.md`](KNOWN_ISSUES.md).
