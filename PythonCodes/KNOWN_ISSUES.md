*AI-generated draft (Claude, Anthropic) — for review. All findings reference version-controlled source.*

# Known issues, quirks, and design notes

Behavioural caveats and deliberate design choices in the `whaletracks`
implementation. These are documented so users can understand *why* the code
behaves as it does and where to be careful when adapting it to new data.

## Edge cases and quirks to be aware of

1. **Detection write branch on an empty middle station.** In
   `cli/run_detection.py`, when some stations yield detections and one yields
   an empty analyzer, the empty-station branch does not write a CSV for that
   station. This is intentional (there is nothing to write) but means an empty
   station produces no output file rather than an empty one.

2. **Possible `IndexError` on the final minute-chunk.** In the multipath loop,
   the end index `one_minute * mp_iter + timescount` can run one past the end of
   the time vector on the last iteration for certain chunk lengths. Guard the
   final chunk if you change the chunking parameters.

3. **Analytic (non-BELLHOP) ranging mode.** With `ranging_source: analytic`,
   `plot_ranges.py` fills the MP3−MP2 timing as `t3 - t2` and logs a warning;
   this path is less validated than the default BELLHOP mode, whose B-station
   ranging output is pinned by `tests/test_plot_ranges_fin.py`. Prefer BELLHOP.

4. **Interactive pick-loop ordering.** The click-labeling loops in
   `cli/verify_calls.py` and `cli/manual_picker.py` process clicks in a rotated
   order (starting from the last click). Every click is still handled; only the
   order differs. These are GUI tools and cannot run headless.

5. **Manual picker records the requested channel.** `manual_picker` stores the
   requested channel string (e.g. `"HHZ,EHZ,ELZ,BHZ,EDH"`) in the CSV `channel`
   column rather than the channel actually returned by the waveform request.

6. **Hardcoded column indices in verification.** `cli/verify_calls.py` appends
   rows using fixed positional indices that assume the detection-CSV schema and
   column count; fragile if the schema changes.

7. **Near-field BELLHOP rows (data, not code).** The ray tables in
   `data/bellhop_arrival_models/` have degenerate entries at very short range
   where the higher multipaths are not well defined (e.g. for B19 the
   `interp_mp3` time is spurious at range 0–10 m, and MP2−MP1 / MP3−MP2 spacings
   show scattered near-field spikes out to ~230 m). `interp_mp1 − interp_d`
   (MP1−Direct) is clean throughout. This does not affect ranging — no whale is
   ranged that close, and within the critical range the measured pair is
   MP1−Direct regardless — so the tables are left as provided. Any code that
   consumes these tables at sub-km range should guard against the near-field
   rows; the tutorial's delay-curve figure omits range < 0.3 km for this reason.

## Fin-whale profile — method decisions

The detection pipeline (`cli/run_detection.py`) ranges to a configurable call
type from a per-call config (`detect_fin.yaml` / `detect_brydes.yaml`). The fin
profile follows the published method of Hilmo & Wilcock (2024) and Hilmo et al.
(2025), with these choices:

1. **No earthquake/T-phase discriminator.** The published method rejects
   earthquakes/T-phases by manual inspection and temporal track association, and
   names automated signal-based rejection as future work, so no amplitude-band
   discriminator is implemented for fin.

2. **Published ranging gate.** A range is attempted only when the centre minute
   has ≥ 2 calls and the surrounding 20-min window has ≥ 10 (Hilmo et al. 2025),
   both in the detection pipeline and in the offline timing→range step
   (`range_estimation.estimate_ranges_from_timings`, via the `ranging:` block in
   `ranges_fin.yaml`). The Bryde's profile uses its own ≥ 1 centre / ≥ 3 window.

3. **Consistent amplitude/SNR reference time.** Amplitude/SNR and the event
   picker use the same `-0.5 * chunk_length` time reference, so amplitude/SNR
   align with the detections.

4. **Fin kernel.** `detect_fin.yaml` uses the published 20→15 Hz, 0.8 s template
   (Hilmo & Wilcock 2024, Table I). Note the shipped fin SNR call band
   `[15.5, 21.5]` predates this and is retained as-is; a 20-based recomputation
   would give `[14.5, 20.5]` — decide before any detection re-run.

5. **Anonymous FDSN access.** Waveforms are fetched with an anonymous
   `Client('IRIS')` (the data are public). *If you fork from older copies that
   contained plaintext credentials, rotate that password.*

6. **Selection grouping/track parameters.** The fin selection (`select_fin.yaml`
   and the library defaults) groups sequential ranges within 1.5 km and 1 h and
   links groups of ≥ 12 ranges with < 3 h gaps into tracks (Hilmo et al. 2025).
   Two additional qualification criteria (mean window call count > 10; < 50 % of
   a group's MP1−Direct ranges equal to zero) are applied as in the published
   workflow. The Bryde's config uses 1.6 km / 2 h.

## Hypothesis-selection — behavioural notes

`detection/hypothesis_selection.py` groups raw ranges, qualifies tracks, links
supertracks, and assigns per-group timing hypotheses by minimising the mismatch
between consecutive groups. Behaviours worth knowing:

- **Single-group supertracks are left unassigned** (`best_hypothesis = NaN`):
  a lone group has no neighbouring group to score against, so it is deferred to
  analyst review.
- **Chunked enumeration.** A supertrack of *n* groups has 3ⁿ hypothesis
  combinations; the assignment streams the enumeration in fixed-size chunks so a
  large supertrack (e.g. 17 groups → 3¹⁷ ≈ 129 M combinations) runs in bounded
  memory (~2 min) with an exact argmin.
- **Monotonic cost shortcut.** The junction cost compares the sum of squared
  range differences (the square root is skipped — it does not change the argmin).
- **Guards.** Degenerate duplicate segment boundaries are skipped; supertracks
  with fewer than two rows are not interpolated (their `interp_range` stays NaN).
- **Per-call interpolation.** `interpolate_call_ranges()` linearly interpolates
  each corrected track's selected range onto the peak time of every detected
  call within the track span; calls outside any track receive no range. This
  per-call table is the ranging pipeline's final product (the input to
  downstream density estimation).
