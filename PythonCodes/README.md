*AI-generated draft (Claude, Anthropic) — for review. All parameters and figures are derived from version-controlled scripts and data.*

# whaletracks — Bryde's whale multipath ranging (Marianas case study)

Detection of Bryde's whale calls from ocean-bottom seismometer / hydrophone
data and estimation of whale-to-station range from the timing of multipath
acoustic arrivals.

The `whaletracks` package is the modernized, config-driven form of the original
scripts: a shared library core, five command-line entry points, and YAML
configuration files that hold every run parameter (nothing is hardcoded in the
source).

## Environment

```bash
conda env create -f environment.yml
conda activate mp_ranging_casestudy
```

This installs the scientific stack (numpy, scipy, pandas, matplotlib, obspy),
`pyyaml`, and dev tools (`pytest`, `ruff`), and performs an editable install of
the local `whaletracks` package (so the `whaletracks-*` commands below are on
your PATH).

## Layout

```
whaletracks/
  common/      constants.py, util.py          # shared constants + conversions
  detection/   detect_calls.py                 # spectrogram / kernel / cross-correlation
               event_analyzer.py               # peak picking -> detection DataFrames
               basic_ranging_model.py          # analytic multipath travel-time model
               manual_picking.py               # helpers for the manual picker (distinct math)
  cli/         run_detection.py                # automated detection + ranging
               plot_ranges.py                  # range estimation + plots
               make_histogram.py               # yearly detection histogram
               verify_calls.py                 # interactive call verification (GUI)
               manual_picker.py                # interactive manual picking (GUI)
  config/      detect_fin.yaml, detect_brydes.yaml   # detection configs (per species)
               ranges_fin.yaml, ranges_brydes.yaml   # range-estimation configs
               verify_calls.yaml, manual_picker.yaml
               Station_info_Marianas_Brydes.csv
tests/         golden-master + regression tests
data/
  bellhop_arrival_models/   per-station BELLHOP ray-arrival tables (shared)
  brydes_whale/             Bryde's detections + range outputs
  fin_whale/                fin detections + range outputs
```

The same pipeline ranges to either species; the two `detect_*.yaml` /
`ranges_*.yaml` pairs differ only in parameters. The fin profile reproduces the
published method of Hilmo & Wilcock (2024) and Hilmo et al. (2025).

## Commands

Each command takes `--config <yaml>` and writes CSVs / figures. Run from the
`PythonCodes` directory so the relative data paths in the configs resolve.

### Automated detection + multipath ranging
```bash
whaletracks-detect --config whaletracks/config/detect_fin.yaml               # all stations
whaletracks-detect --config whaletracks/config/detect_brydes.yaml --station B19
```
Downloads waveforms from IRIS, detects calls, measures SNR/amplitude, and
autocorrelates the detection score to time multipath arrivals. There is one
config per species (`detect_fin.yaml`, `detect_brydes.yaml`); they differ only
in parameters (kernel, frequency bands, event thresholds, autocorrelation
window, and ranging call-count thresholds). Per-station geometry, channel, and
dates come from the station-info CSV named in the config. **Requires network
access.**

### Range estimation + plots
```bash
whaletracks-plot-ranges --config whaletracks/config/ranges_brydes.yaml \
    --station B01 --save ranges_B01.png
```
Matches each autocorrelation minute's strongest multipath timing to a
theoretical timing-vs-distance curve (shared BELLHOP ray table from
`data/bellhop_arrival_models/`, or the analytic model) and writes range
estimates to `data/<species>_whale/`. Offline — runs on the shipped CSVs
(`ranges_fin.yaml` for fin).

### Detection histogram
```bash
whaletracks-histogram --input data/brydes_whale/LongCall_YearPicks/B12_mp_Brydes_Year_LongCall.csv \
    --threshold 5000 --save hist_B12.png
```

### Interactive verification / manual picking (GUI + network)
```bash
whaletracks-verify --config whaletracks/config/verify_calls.yaml
whaletracks-pick   --config whaletracks/config/manual_picker.yaml
```
These open matplotlib windows and use `ginput` for click-based labeling; they
also fetch waveforms from IRIS. They cannot run headless.

## Testing

```bash
MPLBACKEND=Agg python -m pytest -q
```

The suite is a **golden-master safety net**: numeric outputs of the library
core were captured from the original code and are re-checked against the
refactored code, so the refactor is provably output-preserving. `test_plot_ranges.py`
additionally confirms the bellhop-mode range columns for B01 match the committed
`MarianasAutoFiles/Marianas_auto_B01_v2.csv` exactly. GUI/network CLIs are covered
by import / `--help` / config-parse smoke tests only.

## Known issues

Suspected correctness bugs found during the refactor were **documented, not
silently changed** (the refactor preserves outputs exactly). See
[`KNOWN_ISSUES.md`](KNOWN_ISSUES.md).
