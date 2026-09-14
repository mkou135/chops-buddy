# Engine specification

Status: v1 for review. Must be merged before the first commit under `api/src/chops_buddy/engine/` (DoD A16).

Drafted by Claude at Michael's request (DECISIONS #14). Michael owns it by review: any rule he disagrees with is changed here first, then in code. Every rule has an ID (`E-nn`) and the test that will prove it (DoD A2). Test names are the planned names; a rule without a passing test of that name is not implemented.

Sources: `docs/pedagogy/music-practice-methodology.md` (MPM), `docs/pedagogy/passage-mastery-algorithm.mmd`, and the June 2026 requirements doc in cadenceplayground (R4–R10).

## 1. Purpose and boundary

The engine turns a teacher's assignments and a student's self-reported practice logs into the next practice session. It encodes the MPM's passage-mastery procedure: repetition threshold, slow practice, fragment isolation, tempo ladder, and backwards chaining.

Boundary rules:

| ID | Rule | Test |
|---|---|---|
| E-01 | The engine package imports only from the standard library and `pydantic`. | `test_boundary::test_engine_imports_only_stdlib_and_pydantic` |
| E-02 | The engine performs no I/O, reads no clock, and uses no randomness. All ids and timestamps are supplied by the caller. | `test_boundary::test_engine_has_no_io_clock_or_random` |
| E-03 | Every public function is a pure mapping from inputs to outputs: same inputs, byte-identical outputs across 100 calls. | `test_determinism::test_plan_is_byte_identical_across_100_runs` |

The engine does not: choose what to assign (the teacher does), interpret free text (the LLM layer does), or decide whether the student was honest (see §6).

## 2. Vocabulary

- **Target**: one assigned thing to practise. Kind is `scale`, `technique`, or `repertoire`. Carries `target_tempo` (BPM) and an ordered list of **units**.
- **Unit**: the smallest indivisible thing in a target. A single note, or a group that must not be split (triplet, ornament, tightly slurred figure), as decided by the teacher when annotating. Represented as an ordered list of labels, e.g. `["b1", "b2", "b3-triplet", "b4"]`.
- **Fragment**: a contiguous half-open range of unit indices `[start, end)`. The **whole** fragment is `[0, n)`.
- **Phrase**: an optional teacher-annotated fragment boundary (MPM "Chunking"). A target may carry a list of non-overlapping phrases covering `[0, n)`.
- **Level**: `beginner`, `intermediate`, or `advanced`, set per student.
- **Threshold**: the number of consecutive correct repetitions required (MPM "The repetition threshold").
- **Tempo**: BPM. **Working tempo** is the tempo the student is currently prescribed. **Rung** is the fixed increment of the tempo ladder.
- **Mode**: what the student is doing with a target right now: `working`, `isolating`, `chaining`, or `mastered`.
- **Prescription**: one instruction issued for one target in one session: mode, fragment, tempo, threshold, minutes.
- **Session**: an ordered list of **segments**, each wrapping one prescription (or a long-tones warm-up).
- **Log entry**: the student's self-report against one prescription.

## 3. Parameters

All derived tempos are rounded down to a multiple of 4 BPM, floored at 30 BPM, written `round4(x)`.

| ID | Rule | Test |
|---|---|---|
| E-10 | Threshold by level: beginner 3, intermediate 5, advanced 7 (MPM). A target may carry `threshold_override` (3–10) which wins. | `test_params::test_threshold_by_level_and_override` |
| E-11 | Rung = `max(4, round4(0.10 × target_tempo))`. Same for all levels; level already scales the threshold. | `test_params::test_rung_is_ten_percent_min_4` |
| E-12 | Tempo floor = `round4(0.50 × target_tempo)`. The engine never prescribes below the floor (MPM: halving is the effective drop; a second halving is replaced by isolation and chaining). | `test_params::test_tempo_floor_is_half_target` |
| E-13 | Initial working tempo = `start_tempo` if the teacher set it, else `round4(0.60 × target_tempo)`, never below the floor. | `test_params::test_initial_tempo_default_and_override` |
| E-14 | Isolation window = 4 units centred on the reported break unit, clipped to the whole fragment. If the target has phrases, the phrase containing the break unit is used instead. | `test_params::test_isolation_window_and_phrase_override` |
| E-15 | A target must have at least one unit. Targets with zero units are rejected at input validation. | `test_params::test_target_requires_units` |

## 4. Per-target state machine

### 4.1 State

```
TargetState:
  mode:            working | isolating | chaining | mastered
  tempo:           int  (current working tempo, BPM)
  fragment:        (start, end)  (whole when working; a sub-range when isolating; the suffix when chaining)
  chain_base:      (start, end)  (only when chaining: the fragment being rebuilt; whole or an isolated range)
  chain_len:       int  (only when chaining: number of units in the suffix of chain_base)
  fails_here:      int  (consecutive failed entries at the current mode+fragment+tempo)
  mastery_streak:  int  (consecutive qualifying entries at target tempo, see E-33)
```

Initial state: `working`, tempo per E-13, fragment whole, `chain_base` whole, `chain_len 0`, `fails_here 0`, `mastery_streak 0`.

### 4.2 Judging a log entry

| ID | Rule | Test |
|---|---|---|
| E-20 | An entry is a **pass** iff `tempo_used >= prescribed tempo` and `best_consecutive >= threshold`. Anything else is a **fail**. Free text and felt difficulty do not affect pass/fail. | `test_judge::test_pass_requires_tempo_and_threshold` |
| E-21 | An entry whose `prescription_id` does not match the target's current prescription is rejected with an error; state is unchanged. | `test_judge::test_stale_prescription_rejected` |

### 4.3 Transitions on pass

| ID | Rule | Test |
|---|---|---|
| E-30 | `working`, tempo < target: raise tempo by one rung, capped at target tempo (tempo ladder, MPM). `fails_here` resets to 0. | `test_pass::test_working_climbs_one_rung` |
| E-31 | `isolating`: fold back. Fragment becomes whole, mode `working`, tempo unchanged, `fails_here` 0. | `test_pass::test_isolating_folds_back` |
| E-32 | `chaining`, `chain_len < len(chain_base)`: prepend one unit (`chain_len + 1`), fragment becomes the new suffix of `chain_base`, `fails_here` 0. When `chain_len == len(chain_base)` after this step, mode becomes `working` on the whole fragment with tempo unchanged (E-46 covers the isolated case). | `test_pass::test_chaining_prepends_one_unit_then_resumes` |
| E-33 | `working`, tempo == target: the entry is **qualifying**. `mastery_streak` increments. Mode becomes `mastered` when `mastery_streak >= 1` and `felt_difficulty <= 3`, or when `mastery_streak >= 2` regardless of felt difficulty. Otherwise the same prescription is reissued. | `test_pass::test_mastery_requires_ease_or_two_streak` |

### 4.4 Transitions on fail

| ID | Rule | Test |
|---|---|---|
| E-40 | Any fail increments `fails_here` and resets `mastery_streak` to 0. | `test_fail::test_fail_increments_and_resets_streak` |
| E-41 | `working`, tempo > floor: halve. Tempo becomes `max(floor, round4(tempo / 2))`. `fails_here` resets to 0. (MPM "Slow practice".) | `test_fail::test_working_above_floor_halves` |
| E-42 | `working`, tempo == floor, whole fragment, and the entry reports a `break_unit`: isolate. Mode `isolating`, fragment per E-14, tempo unchanged, `fails_here` 0. | `test_fail::test_working_at_floor_with_break_isolates` |
| E-43 | `working`, tempo == floor, and no `break_unit` reported: this is a **stall**. Go to `chaining` with `chain_base` whole, `chain_len 1` (fragment = last unit), tempo unchanged, `fails_here` 0. | `test_fail::test_working_at_floor_without_break_chains` |
| E-44 | `isolating`, `fails_here` reaches 2: stall. Go to `chaining` with `chain_base` = the isolated fragment, `chain_len 1`, tempo unchanged, `fails_here` 0. A first fail while isolating reissues the same prescription. | `test_fail::test_isolating_two_fails_chains_fragment` |
| E-45 | `chaining`: a fail reissues the same suffix. `chain_len` never decreases. | `test_fail::test_chaining_fail_reissues` |
| E-46 | When chaining completes a `chain_base` that is not the whole fragment, the fold-back of E-31 applies: fragment becomes whole, mode `working`, tempo unchanged. | `test_fail::test_chain_of_isolated_fragment_folds_back` |
| E-47 | `mastered` targets accept no log entries; the API must not issue prescriptions for them. Teachers reset a target by re-assigning it, which returns it to the initial state. | `test_fail::test_mastered_accepts_no_entries` |

### 4.5 Walkthrough

Target: 8 units, target tempo 120, intermediate (threshold 5). Rung 12, floor 60, start 72.

1. Prescribed: working, whole, 72. Student logs 5-in-a-row at 72 → pass → tempo 84 (E-30).
2. Logs 3-in-a-row at 84 → fail → tempo 60 (E-41).
3. Logs 2-in-a-row at 60, break at unit 5 → fail at floor with break → isolating [3,7) at 60 (E-42).
4. Logs 5-in-a-row on [3,7) at 60 → pass → working, whole, 60 (E-31).
5. Logs 5-in-a-row at 60 → pass → 72 → 84 → 96 → 108 → 120 over five sessions (E-30).
6. Logs 5-in-a-row at 120, difficulty 4 → qualifying, streak 1, reissued (E-33).
7. Logs 5-in-a-row at 120, difficulty 2 → mastered (E-33).

## 5. Session composer

Inputs: student (`level`, `instrument_family`), the list of assigned targets with their current state, `duration_minutes ∈ {10, 20, 30}`.

| ID | Rule | Test |
|---|---|---|
| E-50 | Segment order is fixed: long tones, scales, technique, repertoire (MPM "Lesson Structure"). Within a kind, targets keep assignment order. | `test_compose::test_segment_order_fixed` |
| E-51 | A long-tones segment is included iff `instrument_family ∈ {wind, brass, voice}`. It has no state machine and a fixed prescription: "sustain each note of the first assigned scale, 8 counts, at 60 BPM" (or the C major scale if no scale is assigned). | `test_compose::test_long_tones_by_instrument_family` |
| E-52 | Mastered targets are excluded from sessions. | `test_compose::test_mastered_excluded` |
| E-53 | Minutes are allocated by kind: long tones 15%, scales 25%, technique 20%, repertoire 40%. Kinds with no eligible target release their share to the remaining kinds proportionally. | `test_compose::test_kind_allocation_and_redistribution` |
| E-54 | Within a kind, minutes are split by weight: 1 for `working`, 2 for `isolating` or `chaining`. Each segment gets at least 2 minutes; the rounding remainder goes to the last segment of the session. Segment minutes sum to `duration_minutes`. | `test_compose::test_within_kind_weights_and_sum` |
| E-55 | If the split would give any segment fewer than 2 minutes, targets are dropped from the end of their kind's list (lowest assignment order first is kept) until every remaining segment has at least 2 minutes. Dropped targets are listed in the plan's `deferred` field. | `test_compose::test_drops_targets_when_too_short` |
| E-56 | With no eligible targets and no long tones, the composer returns an error `nothing_to_practise`; it never returns an empty session. | `test_compose::test_nothing_to_practise_error` |
| E-57 | Each prescription's instruction text is produced by a fixed template per mode. Templates contain no adjectives about the student and never mention streaks, points, or badges (Designing for Motivation, §1). | `test_compose::test_instruction_templates` |

Templates (exact strings are part of the spec):

- working: `Play {fragment_label} at {tempo} BPM. Goal: {threshold} correct in a row. A mistake resets the count.`
- isolating: `Isolate {fragment_label} at {tempo} BPM. Goal: {threshold} correct in a row, then it goes back into context.`
- chaining: `Build from the end: play the last {chain_len} unit(s) ({fragment_label}) at {tempo} BPM. Goal: {threshold} correct in a row, then add the unit before.`
- long tones: `Long tones: sustain each note of {scale_title}, 8 counts each, at 60 BPM. Listen for a steady centre.`

`{fragment_label}` is `"the whole passage"` for the whole fragment, else `"units {first}–{last}"` using the unit labels.

## 6. Log ingestion

Log entry schema (one per prescription):

```
LogEntry:
  prescription_id:   str
  tempo_used:        int   (BPM, 20–300)
  best_consecutive:  int   (0–50)
  break_unit:        int | None   (index into the target's units, within the prescribed fragment)
  felt_difficulty:   int   (1 easy – 5 very hard)
  free_text:         str | None   (max 500 chars; ignored by the engine, read by the LLM layer)
```

| ID | Rule | Test |
|---|---|---|
| E-60 | Fields are validated to the ranges above; out-of-range entries are rejected without changing state. | `test_ingest::test_field_ranges` |
| E-61 | `break_unit` outside the prescribed fragment is rejected. | `test_ingest::test_break_unit_must_be_in_fragment` |
| E-62 | The engine trusts the numbers as reported. There is no plausibility filter; the only guard against an over-generous self-report is E-33's ease-or-repeat rule for mastery. | `test_ingest::test_numbers_trusted_as_given` |
| E-63 | Entries are applied in the order given; applying the same list twice from the same initial state yields the same final state. | `test_ingest::test_apply_is_order_dependent_and_repeatable` |

## 7. Determinism contract

| ID | Rule | Test |
|---|---|---|
| E-70 | The plan hash is SHA-256 over canonical JSON (sorted keys, no whitespace) of the segment list with fields `kind, target_id, mode, fragment, tempo, threshold, minutes, instruction`. Caller-supplied ids and timestamps are excluded. | `test_determinism::test_plan_hash_excludes_ids_and_timestamps` |
| E-71 | Two plans with equal hashes are equal for every field a student sees. | `test_determinism::test_equal_hash_means_equal_visible_plan` |

## 8. Resolved questions

The ten questions from the skeleton, with the rule that answers each:

1. Tempo ladder increment → E-11 (10% of target, min 4 BPM, all levels).
2. Stalled → E-43 (fail at floor with no break point) and E-44 (two fails while isolating).
3. Isolation boundary → E-14 (4-unit window; teacher phrase wins).
4. Indivisible units → §2 and E-15 (units are the teacher's list; a group is one unit; at least one required).
5. Threshold source → E-10 (per student, per-target override).
6. Duration allocation → E-53 to E-55.
7. After mastery → E-52 and E-47 (excluded; teacher re-assigns to reset).
8. Long tones → E-51 (wind, brass, voice).
9. Self-report trust → E-20, E-33, E-62 (trusted; mastery needs ease or two in a row).
10. Determinism contract → E-70, E-71.

## 9. Out of scope for the engine

Spaced repetition, interleaving, rhythm-comprehension techniques, accompaniment, and any interpretation of free text. These are listed as Later/Advanced in the MPM or belong to other layers.
