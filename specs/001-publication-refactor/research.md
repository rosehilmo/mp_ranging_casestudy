*AI-generated draft (Claude, Anthropic) — for review. All parameters and figures are derived from version-controlled scripts and data.*

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
- **Fin vs Bryde's threshold variations kept.** Published fin ranging attempts a
  range when the center minute has ≥ 2 calls and the 20-min window has ≥ 10;
  Bryde's uses center ≥ 1 / window ≥ 3. Both retained per PI ("keep the
  variations").

## Data-layout decisions

- **One shared station table** `data/Station_info_Marianas.csv` = the 7 published
  good-data OBS, used by both species. Adopted the fin table's accurate
  per-station dates over Bryde's uniform placeholder; dropped unpublished extra
  stations.
- **Standardized output names**: `{station}_mp.csv`, `auto_{station}_mp.csv`,
  `Marianas_auto_{station}_v2.csv` (matches the published code).
- **Data reorganized by species** under `data/{fin_whale,brydes_whale}` with a
  shared `bellhop_arrival_models/`. Orphan `All_Brydes_verified.csv` moved from
  the `PythonCodes/` root into `data/brydes_whale/`.

## Documentation decisions

- **Tutorial is Quarto (.qmd)**, matching the `Sample documentation_NEAREST/`
  chapter house style (a stub the tutorial fills), with student-facing **Plotly**
  figures and cross-references. AI disclosure via YAML metadata + header callout
  (PI chose the metadata form over monospace body text).
- **Literature handling**: JASA 2024 PDF is ASA copyright → `literature/`
  gitignored; cite, don't reproduce. ESR 2025 is CC-BY. `references.bib` holds
  factual bibliographic metadata only.

## Security

- Upstream `MP_Marianas_automation.py` contained **hardcoded FDSN credentials**
  (plaintext). Refactored to anonymous `Client('IRIS')` (public data). **The
  exposed password must still be rotated by the PI** — outside the repo.
