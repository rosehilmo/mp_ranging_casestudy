*Author: Rose Hilmo. Drafted with AI assistance (Claude, Anthropic), then edited and verified by the author. All parameters and figures are derived from version-controlled scripts and data.*

# Research & Decisions: Publication-readiness refactor

Method and engineering decisions, with rationale. Back-filled from the refactor.

## Locked decisions (PI)

- **Full repackage** into an installable `whaletracks` package (not a loose
  scripts folder). Rationale: portability + console entry points + testability.
- **Preserve outputs exactly.** The refactor may not change algorithm logic or
  numeric results; suspected bugs are documented in `KNOWN_ISSUES.md`, never
  silently fixed. Rationale: the published case-study results must stand.
- **Keep conda.** Upstream is conda-based; the refactor preserves it
  (`environment.yml`) rather than migrating to the lab-default `uv`. Rationale:
  minimize migration risk on a preserve-exactly refactor. Consequence: the stale
  `environment_1.yml` and an unused `uv.lock` were removed so there is one
  deterministic environment definition.
- **Species scope = fin + Bryde's** (not blue). Both were studied on these OBS.
  After the 2026-10-05 trim only the Bryde's *configs* remain (as adaptation
  examples); the Bryde's data are no longer shipped.
- **Python-only demonstration (2026-10-05).** The repository ships one
  single-station worked example (B20 fin whale, `CORTADO_TEST`) rather than the
  published multi-station analysis. `MATLABCodes/`, the R density scripts, the
  Bryde's data, and all non-B20 fin data were removed. Rationale: the PI wants an
  adaptable, easily-implementable Python demonstration for other researchers,
  shipping the bare minimum data needed to run the code and the tutorial.
  Consequences: the whole ranging process (detection → autocorrelation → range
  estimation → hypothesis selection → per-call interpolation) is Python;
  density estimation is explicitly out of scope; the Bryde's B01 golden test and
  the MATLAB-reference golden for the selection port were dropped with their
  inputs. The pre-trim state is preserved at tag `full-dataset-pre-cleanup`, and
  **git history was deliberately not purged** (PI decision) — a fresh clone's
  working tree is minimal, but `git log` still contains the removed files.
- **Destructive-change procedure (PI-endorsed).** Branch, tag the pre-change
  state as a restore point, drive deletion from a real dependency scan, and
  verify with `pytest` + `quarto render` before committing.

## Method decisions

- **Autocorrelation, not summed-spectrogram, for multipath spacing.** Hilmo &
  Wilcock (2024) tested spectrogram stacking as an alternative; it performed
  poorly and is **deprecated** — the tutorial and docs describe only the
  autocorrelation approach (PI direction, 2026-09-25).
- **BELLHOP produces the final ranges.** `basic_ranging` (analytic straight-ray)
  is a first-order helper used *only* to set the multipath search window in
  `run_detection` (`dt_down = max(mp_interp − t0) + 0.2`), not for ranges. The
  earlier framing of the analytic model as "the forward model" was corrected.
- **Multipath physics (author-confirmed).** Direct path D plus multipaths MPn,
  where MPn reflects *n* times off both the sea surface and the sub-seafloor
  reflector; refraction bends rays away from the seafloor so the set of paths
  reaching the OBS depends on range. (Corrected from an earlier surface-multiple
  + separate-basement-path description.)
- **Drop the unpublished T-phase amplitude discriminator.** The experimental
  `MultipathRanging_Fins.py` rejected T-phases via `db_amps+5 > db_amps_eq`; this
  was never published (both papers handled T-phases/earthquakes manually and via
  track association). Dropped as a deliberate, documented deviation.
- **Fin ranging gate = the published 2025 criteria, at detection AND offline
  ranging (PI, 2026-09-29).** A fin window is ranged only when its centre minute
  (±30 s) holds ≥ 2 detected calls and the surrounding 20-min window holds ≥ 10
  (Hilmo et al. 2025). Originally applied only in `run_detection`; the PI
  directed applying it in the offline timing→range step too
  (`estimate_ranges_from_timings`, `ranging:` block in `ranges_fin.yaml`;
  B20 CORTADO_TEST output regenerated, 7140 → 7105 rows). Bryde's keeps its
  legacy gates unchanged (detection: centre ≥ 1 / window ≥ 3; offline ranging:
  centre ≥ 1 only — B01 golden output untouched). The paper's ≥ 12-range
  track-grouping remains a separate downstream density-workflow step.
- **Ranging logic factored into `whaletracks/detection/range_estimation.py`**
  (2026-09-28): side-effect-free functions (`bellhop_timings`,
  `estimate_ranges_from_timings`) shared by the `plot_ranges` CLI and the
  tutorial; verified byte-identical to the pre-factor CLI output at the time
  for fin B19 and Bryde's B01. **B20 is the worked/tested fin station
  everywhere (PI, 2026-09-29)**; the B19 and Bryde's files were removed in the
  2026-10-05 trim.
- **Tutorial worked example = station B20, CORTADO_TEST dataset** (PI,
  2026-09-28), replacing B19. Optional tz-safe `valid_start`/`valid_end` bounds
  were added to the ranging step; B20 uses `valid_end = 2013-02-01` to exclude
  the Feb 2013+ airgun survey → 7105 ranged windows (Mar 2012 – Jan 2013,
  under the published ≥2/≥10 ranging gate), matching Hilmo et al. (2025).
- **Unphysical model values are filtered out of figures, never accommodated by
  rescaling axes** (PI preference, 2026-09-28). The tutorial delay-curve masks
  BELLHOP near-field artifacts (< 0.3 km; see `KNOWN_ISSUES.md`, "Edge cases
  and quirks" → *Near-field BELLHOP rows*); the data
  files themselves are untouched (preserve-exactly).

## Data-layout decisions

- **One shared station table** `data/Station_info_Marianas.csv` = the 7 published
  good-data OBS, used by both species. Adopted the fin table's accurate
  per-station dates over Bryde's uniform placeholder; dropped unpublished extra
  stations.
- **Standardized output names**: `{station}_mp.csv`, `auto_{station}_mp.csv`,
  `Marianas_auto_{station}_v2.csv` (matches the published code).
- **Data reorganized by species** under `data/{fin_whale,brydes_whale}` with a
  shared `bellhop_arrival_models/`. Orphan `All_Brydes_verified.csv` moved from
  the `PythonCodes/` root into `data/brydes_whale/`. *(Since the 2026-10-05 trim
  only `data/fin_whale/` — the B20 `CORTADO_TEST` set — the station table, and
  the BELLHOP tables are shipped.)*

## Provenance

- **Sidecar YAML per output** (`<output>.provenance.yaml`, 2026-10-08, T025).
  Chosen over an in-CSV comment header (which would change the output bytes and
  break the golden-master comparisons) and over a central run registry (which
  goes stale the moment a file is copied): the sidecar travels with the file,
  is readable without the package installed, and leaves the output untouched.
  It records the command + code version + git commit, the config and its
  SHA-256 plus the parameters actually applied, the source
  network/station/channel/time span, and a SHA-256 for every input.
- **A manifest never claims a run that did not happen.** Files the repository
  ships but did not generate — the B20 detection inputs, and the
  analyst-corrected selection table — carry `command: null` and a note saying
  where they came from, instead of a command and code version that would imply
  reproducibility they do not have.
- Re-running a stage reproduces the output bytes and changes only
  `generated.utc`, so a manifest diff confined to that field is positive
  evidence that a result reproduced.

## Documentation decisions

- **Tutorial is Quarto (.qmd)**, matching the `Sample documentation_NEAREST/`
  chapter house style (a stub the tutorial fills), with student-facing **Plotly**
  figures and cross-references. AI disclosure via YAML metadata + header callout
  (PI chose the metadata form over monospace body text).
- **Tutorial figures render as static PNGs** (Plotly + kaleido, `renderer =
  "png"`, scale 2), a deliberate deviation from the interactive-Plotly default
  (PI decision, 2026-09-26): the JupyterLab file preview sandboxes JavaScript,
  so interactive divs never paint and leave layout gaps. All figures are
  colourblind-safe (Okabe–Ito palette + line-style/marker variation; see
  constitution Figure Standards).
- **Literature handling**: JASA 2024 PDF is ASA copyright → `literature/`
  gitignored; cite, don't reproduce. ESR 2025 is CC-BY. `references.bib` holds
  factual bibliographic metadata only.

## Security

- Upstream `MP_Marianas_automation.py` contained **hardcoded FDSN credentials**
  (plaintext). Refactored to anonymous `Client('IRIS')` (public data). **The
  exposed password must still be rotated by the PI** — outside the repo.
