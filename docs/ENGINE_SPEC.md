# Engine specification

Status: DRAFT. Must be merged before the first commit under `api/src/chops_buddy/engine/` (DoD A16).

Author: Michael. Reviewer: Claude. Every rule gets an ID (`E-nn`) and, once implemented, the name of the test that proves it (DoD A2).

Sources: `docs/pedagogy/music-practice-methodology.md`, `docs/pedagogy/passage-mastery-algorithm.mmd`.

## 1. Purpose and boundary

<!-- What the engine is responsible for, and what it is not. State explicitly: no I/O, no model, no clock; every function is a pure mapping from inputs to outputs. -->

## 2. Vocabulary

<!-- Define: target, unit (indivisible group), fragment, level, threshold, tempo, rung, session, segment, prescription, log entry. One sentence each. -->

## 3. State machine

### 3.1 States

<!-- WorkAtTempo, ClimbLadder, Slow, Isolate, BackChain, Mastered. What each state means and what data it carries. -->

### 3.2 Transitions

<!-- One rule per transition. Format:

E-01  From WorkAtTempo, when a log entry reports best-consecutive >= threshold at current tempo and current tempo == target tempo, go to Mastered.
      Test: (fill in when implemented)
-->

## 4. Open questions to resolve here

Each answer becomes a rule with an ID.

1. **Tempo ladder increment.** Fixed BPM or percentage? Does it vary by level?
2. **Stalled.** How many failed log entries at halved tempo before backwards chaining?
3. **Isolation boundary.** Teacher-annotated fragments, a fixed window around the reported break point, or both?
4. **Indivisible units.** How is a target's unit list represented? What happens when the teacher annotates none?
5. **Threshold source.** Does the teacher set level per student or per target?
6. **Duration allocation.** How is session time split across segments when a target is mid-escalation?
7. **After mastery.** Does a mastered target rotate out, get maintenance reps, or stay until the teacher removes it?
8. **Long tones.** Which instruments include a long-tone segment, and how long?
9. **Self-report trust.** Does a contradictory entry (threshold met at target tempo, felt difficulty 5) advance state?
10. **Determinism contract.** Which fields are excluded from the plan hash used by the byte-identical test (DoD A3)?

## 5. Session composer

<!-- Inputs, ordering rule (long tones → scales → technique → repertoire), how prescriptions are worded, what the composer does when there are zero assignments. -->

## 6. Log ingestion

<!-- The self-report schema (tempo used, best consecutive correct, break point as unit index, felt difficulty 1–5, free text), validation rules, and which fields the engine ignores (free text is for the LLM layer only). -->

## 7. Rule table

| ID | Rule | Test |
|---|---|---|
| E-01 | | |
