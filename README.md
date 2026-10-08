*AI-generated draft (Claude, Anthropic) — for review. All parameters and figures are derived from version-controlled scripts and data.*

# Multipath whale-call ranging — a Marianas fin-whale case study

Estimate the **horizontal range from an ocean-bottom seismometer (OBS) to a
calling baleen whale** using the timing of multipath acoustic arrivals — the
direct path plus echoes that bounce off the sea surface and a sub-seafloor
reflector. One instrument, no array required.

This repository ships the **Python implementation** of the method of
[Hilmo & Wilcock (2024)](https://doi.org/10.1121/10.0024615) and
[Hilmo et al. (2025)](https://doi.org/10.3354/esr01439), together with a worked,
end-to-end **demonstration** on a single Marianas fin-whale station (**B20**) and
a tutorial that walks through the physics and the code.

> **Demonstration scope.** The shipped data are a `CORTADO_TEST` subset for one
> station, included so the pipeline and tutorial run end to end. They are **not**
> the published dataset and do **not** reproduce the paper's ranges or densities.
> Distance-sampling density estimation is downstream of ranging and out of scope
> here.

## What the pipeline does

```
waveforms ──► detect calls ──► autocorrelate the detection score ──► match delays
(FDSN/IRIS)   (spectrogram      (multipath delays, 20-min window)    to BELLHOP
               cross-correlation)                                     travel-time
                                                                      tables
                                                                         │
                        per-call ranges ◄── analyst review ◄── group into tracks,
                        (the final product)                   pick one hypothesis
```

Everything after the first arrow runs **offline** on the shipped CSVs — you do
not need network access to reproduce the demonstration or render the tutorial.

## Quickstart

You need [conda](https://docs.conda.io/projects/miniconda/en/latest/)
(or [mamba](https://mamba.readthedocs.io/), which solves much faster). Nothing
else — the environment file pulls in Python, the scientific stack, Quarto and
the test tools.

```bash
git clone https://github.com/rosehilmo/mp_ranging_casestudy.git
cd mp_ranging_casestudy/PythonCodes

conda env create -f environment.yml      # or: mamba env create -f environment.yml
conda activate mp_ranging_casestudy

# One-time: fetch the Chromium that Plotly uses to export static figures.
kaleido_get_chrome
```

Check the install — this runs the whole offline pipeline against the shipped
data and should take a couple of minutes:

```bash
MPLBACKEND=Agg python -m pytest -q         # expect: 35 passed
```

Then reproduce the worked example and read the tutorial:

```bash
# Measured multipath delays -> ranges (writes a CSV + a provenance sidecar)
whaletracks-plot-ranges --config whaletracks/config/ranges_fin.yaml --station B20

# Render the tutorial to a self-contained HTML page, then open it
quarto render tutorials/multipath_ranging.qmd
```

That last command **builds** `tutorials/multipath_ranging.html`, which then opens
in any browser — it is self-contained (no network, no CDN) and carries all its
figures inline, so it can be emailed or shared as a single file. The HTML is a
build artifact and is deliberately not committed, so a fresh download does not
contain it until you render it once.

**Run commands from the `PythonCodes` directory**: the config files use data
paths relative to it.

### Working in R / RStudio

Quarto is language-agnostic, so `.qmd` is **not** a Python-only format: RStudio
and Positron open, edit and render `tutorials/multipath_ranging.qmd` as a
first-class document, and you get the usual outline, visual editor and Render
button.

What R *cannot* do is execute it. This tutorial declares `jupyter: python3` and
all sixteen of its code cells are `{python}` — they import the `whaletracks`
package and work on the shipped data. There is no R or `knitr` code in the
document, so **rendering always needs the conda environment above**, whichever
editor starts it. Point Quarto at that environment in one of two ways:

```bash
# Either: activate the environment, then launch RStudio from that same shell
conda activate mp_ranging_casestudy && rstudio

# Or: tell Quarto explicitly which Python to use
export QUARTO_PYTHON="$(conda run -n mp_ranging_casestudy which python)"
```

Without this, the render stops at the first cell with
`ModuleNotFoundError: No module named 'plotly'` — that error means Quarto found
the wrong Python, not that anything is broken.

If you only want to *read* the tutorial, you need neither R nor Python — but the
HTML is not shipped in the repository, so it has to be rendered once (by you, or
by a colleague who then sends you the single self-contained file).

## Repository layout

| Path | What it is |
|---|---|
| `PythonCodes/` | everything runnable — see its [README](PythonCodes/README.md) for the full command reference |
| `PythonCodes/whaletracks/` | the installable package: library core, six CLI entry points, YAML configs |
| `PythonCodes/tutorials/` | the Quarto tutorial (`multipath_ranging.qmd`) and its bibliography |
| `PythonCodes/data/` | station table, BELLHOP travel-time tables, and the B20 demonstration set |
| `PythonCodes/tests/` | golden-master and regression tests |
| `PythonCodes/KNOWN_ISSUES.md` | known quirks and deliberate design decisions |
| `specs/`, `.specify/` | the project's specifications, task history, and research constitution |

## Adapting it to your own data

The pipeline is call-type- and site-agnostic: supply a station table, a
per-station BELLHOP travel-time table, and a detection kernel for your call, and
the same code ranges to it. Every run parameter lives in a YAML config — nothing
is hardcoded. The fin configs are the worked example and the Bryde's configs show
a second parameterisation. See *Adapting to your own data* in the
[package README](PythonCodes/README.md).

## Provenance

Each generated CSV is written with a `*.provenance.yaml` sidecar recording the
command, code version, config (with a hash), the network/station/channel/time
span of the source data, and a SHA-256 for every input — so any output can be
traced to the exact bytes and parameters that produced it.

## Citation

If you use this method, please cite the papers rather than this repository:

- Hilmo, R., and Wilcock, W. S. D. (2024). "Estimating distances to baleen whales
  using multipath arrivals recorded by individual seafloor seismometers at full
  ocean depth," *J. Acoust. Soc. Am.* **155**(2), 930–951.
  doi:[10.1121/10.0024615](https://doi.org/10.1121/10.0024615)
- Hilmo, R., Harris, D., and Wilcock, W. S. D. (2025). "Applying distance sampling
  to estimate densities of fin whale calls recorded by ocean bottom seismometers
  in the Marianas region," *Endangered Species Research* **58**, 159–174.
  doi:[10.3354/esr01439](https://doi.org/10.3354/esr01439) (open access, CC BY 4.0)

## License

[MIT](LICENSE). The shipped data are a demonstration subset; see the scope note
above before drawing scientific conclusions from them.
