*AI-generated draft (Claude, Anthropic) — for review. All parameters and figures are derived from version-controlled scripts and data.*

# Plan: Port the semi-automated multipath hypothesis selection to Python

**Spec**: `specs/002-hypothesis-selection/spec.md`
**Created**: 2026-09-29
**Status**: In progress

## Approach

Faithful port of `clean_group_ranges.m` (+ the per-call interpolation script)
into `whaletracks`, preserving the MATLAB behaviour exactly — including its
quirks (supertrack boundary handling, single-group `best_hypothesis = NaN`,
first-minimum tie-breaking). Enumeration order for hypothesis combinations uses
`itertools.product`, which matches MATLAB `combinations` (first variable slowest),
so argmin tie-breaks identically. A guard errors out if a segment's 3^n
exceeds a configurable cap (the MATLAB >18-group midpoint split keeps n small
in practice).

The interactive analyst loop (accept / override / reject per group) stays
manual: the port ships the automated selection; the review is a thin CLI loop
over the automated output (matplotlib + prompt), usable only with a display —
same operational shape as the MATLAB original.

## Structure

```text
whaletracks/detection/hypothesis_selection.py   # pure functions:
    filter_ranges()        # step 1 (25-km / >=1-call / 40-km-saturation filter)
    group_ranges()         # step 2 (1.6 km / 1 h walk)
    qualify_groups()       # step 3 (use_track)
    build_supertracks()    # step 4 (2 h gap + >18 midpoint split)
    assign_hypotheses()    # step 5 (3^n enumeration, RMS junction cost)
    select_hypotheses()    # steps 1-5 composed -> full table + 4 new columns
    interpolate_call_ranges()  # step 7 (per-supertrack interp onto peak_time)
whaletracks/config/select_fin.yaml              # fin thresholds (>11 / >10)
whaletracks/config/select_brydes.yaml           # Bryde's thresholds (>6 / >2)
whaletracks/cli/select_hypotheses.py            # whaletracks-select CLI
tests/test_hypothesis_selection.py              # synthetic + golden (skipif)
tutorial section after #sec-results             # B20 worked example
```

## Constitution Check

- [x] Preserve-exactly: quirks reproduced; deviations (if any forced) →
      `KNOWN_ISSUES.md`
- [x] Config versioned: all thresholds in `select_{species}.yaml`
- [x] Figure standards: tutorial figure Okabe–Ito, static PNG
- [x] Quality checks: pytest + ruff + quarto render before commit
- [ ] Golden-master: **pending PI's MATLAB reference run** — until then the
      port is verified by synthetic structural tests only (documented gap)

## Open Questions

- [ ] Golden reference: PI to run `clean_group_ranges.m` on the repo's B20
      CORTADO_TEST input and commit the automated output (B20 everywhere per
      PI 2026-09-29; memory caveat in the spec).
- [ ] Disposition of the two Bryde's figure scripts (histograms, monthly
      density) — port later or fold into the R/density segment?
- [ ] The MATLAB fin filter keeps `sum_calls >= 1`; with feature 001's new
      2/10 ranging gate the B20 input is already gated — confirm thresholds
      still make sense for B20 (they only tighten, so the port keeps them).
