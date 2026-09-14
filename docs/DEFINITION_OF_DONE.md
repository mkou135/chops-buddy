# Definition of Done — v0.1

Status: approved 2026-09-14. Changes to this document require a DECISIONS.md entry.

## The stop sentence

**v0.1 is done when a git tag `v0.1.0` exists whose README links to a live API on AWS App Runner, a green CI run on `main`, and a committed eval results table covering at least three dated runs with per-case failures shown, and every acceptance criterion below is ticked in the release PR with its named evidence (a CI job or a linked test counts).**

Anything not listed under "In scope" is out, even if it seems small.

## In scope

### Engine (deterministic core, pure Python, no I/O)
- Passage-mastery state machine per target: repetition threshold by level (3/5/7), slow-on-failure (halve tempo), isolate fragment, tempo ladder with fixed increment, backwards chaining escalation that advances by indivisible units, mastered when the threshold holds at target tempo.
- Session composer: given assignments, per-target state, and chosen duration, produce an ordered session (long tones where applicable → scales → technique → repertoire) with per-segment prescriptions.
- Practice log ingestion: a self-report entry per target (tempo used, best consecutive correct, break point as unit index, felt difficulty 1–5, optional free text) advances the state machine.

### LLM layer (optional, above the engine)
- One task: given engine state, the last N log entries including free text, and the engine's own default plan, propose the next session as structured JSON plus a one-paragraph rationale.
- Deterministic validator: rejects or repairs proposals that break methodology rules (illegal tempo moves, lowered threshold, skipped escalation, unassigned targets, wrong segment order, durations that don't sum, chaining that splits an indivisible unit). Every rule has a test.
- Feature flag: with no API key configured, the API returns the engine's plan and reports `source: "engine"`.

### Eval suite (a v0.1 requirement, not v0.2)
- Golden dataset of ≥50 cases in the repo. Each case = input fixture + assertions + an author note on why it exists.
- Categories, each with ≥5 cases: happy path, stalled student, ambiguous free text, contradictory self-report, level boundaries, indivisible units, empty/first session, teacher override present.
- Runner: `python -m evals` produces a JSON result. CI runs it on every PR touching the prompt, validator, or evals, and weekly on `main`.
- Published results: append-only `api/evals/results/`, one file per run, plus a generated README table (date, model, prompt version, pass rate, top failing categories). Regressions are kept, not deleted.
- Metrics: proposal legality rate (before repair), repair rate, agreement with engine on decisive cases, per-category pass rate.

### API (FastAPI)
- Supabase Auth JWT verified per request; role and tenant resolved from a `profiles` table.
- Student: list my assignments, get next session, submit a practice log, view my history.
- Teacher: roster CRUD, assign targets (level, target tempo, indivisible-unit annotations), view a student's engine state and history, override next session.
- CRM: schools, teacher↔school membership, students belong to a school, lessons (scheduled, with notes), attendance per lesson, parent/guardian contacts, terms (date ranges that scope lessons).
- Authorisation tests: teacher A cannot read teacher B's student; student cannot read another student; school-scoped listing respects membership.
- OpenAPI docs served; README links them.

### Data
- Alembic migrations from zero; CI applies them to a fresh Postgres service container.
- Seed script producing one demo school, two teachers, six students, assignments, and 30 days of logs.

### Client (thin, deliberately unremarkable)
- Student: sign in, see next session, log a session, see history.
- Teacher: roster, assign, view student, CRM screens (schools, lessons, attendance, contacts, terms). Plain forms and tables; no design investment.

### Infrastructure
- Dockerfile; image pushed to ECR from CI; App Runner service defined in Terraform; `terraform plan` on PR, `apply` on `main`; OIDC role, no static keys.
- Live URL with `/health` and `/docs`.

### Documentation
- `docs/ENGINE_SPEC.md` written and merged before engine code.
- `docs/DECISIONS.md` append-only.
- Methodology and Motivation documents version-controlled in `docs/pedagogy/`.
- README: what it is, why it exists, architecture diagram, eval results table, how to run.

## Out of scope (explicitly)

- Microphone, pitch detection, audio of any kind; importing cadenceplayground outcomes.
- Accompaniment / backing tracks; the "song they chose" library.
- Spaced repetition scheduling, interleaving, rhythm-comprehension techniques.
- Gamification beyond a plain "last practised" date. No streaks, points, badges.
- Messaging, invoicing, payments, parent login (contacts are records, not users).
- Mobile app.
- RAG, vector search, agents with tools. One prompt, one structured output.
- A judge model for grading. All grading is deterministic.
- Multi-region, autoscaling policy tuning, custom domain, CDN.
- Any change to Woodshed.

## Acceptance criteria

| ID | Criterion | Evidence |
|---|---|---|
| A1 | Engine has zero imports outside stdlib + pydantic; 100% branch coverage on the state machine module. | CI coverage job |
| A2 | Every rule in ENGINE_SPEC has a named test; the spec table lists the test name. | Spec doc + `pytest -k` |
| A3 | Same input → byte-identical session plan across 100 runs. | Property test |
| A4 | API returns a valid session with `LLM_API_KEY` unset. | Integration test |
| A5 | Validator rejects each listed rule class; each has a fixture. | pytest |
| A6 | ≥50 golden cases, ≥5 per category, each with an author note. | `python -m evals --count` in CI |
| A7 | Eval runner exits non-zero if overall pass rate drops >5 points vs the last `main` run. | CI job |
| A8 | `api/evals/results/` has ≥3 dated runs; README table regenerated by CI, failures listed per run. | Repo inspection |
| A9 | Auth: 401 without token, 403 across tenant; 6 named authorisation tests pass. | pytest |
| A10 | Migrations apply from an empty DB in CI; seed script runs in <30 s. | CI job |
| A11 | Terraform plan is clean on `main`; apply from CI produces the running service. | Actions log + URL |
| A12 | `GET /health` on the live URL returns 200 with the commit SHA. | curl in release PR |
| A13 | Client: student completes the full loop (sign in → next session → log → history) against the live API. | Screen recording in release PR |
| A14 | Client: teacher can create school, add student, assign, schedule lesson, mark attendance, add contact, add term. | Screen recording |
| A15 | DECISIONS.md has ≥25 entries, each with who / what / what reverses it. | Repo inspection |
| A16 | ENGINE_SPEC merged before the first engine commit. | Git history |
| A17 | The chops-buddy prototype code is either the live client or removed; no "not yet wired" README remains. | Repo inspection |
| A18 | README shows the architecture diagram and eval table above the fold. | Repo inspection |

## Sequencing (16 weeks, ~6 h/week)

| Milestone | Weeks | Deliverable | Exit test |
|---|---|---|---|
| M0 Foundations | 1 | Repo restructure, this DoD, DECISIONS seed, ENGINE_SPEC, CI skeleton | A16 |
| M1 Engine | 2–4 | State machine + composer + log ingestion, TDD, no DB | A1–A3 |
| M2 Data + API core | 5–6 | Schema, migrations, auth, student + teacher assignment endpoints | A9, A10 |
| M3 LLM + evals | 7–8 | Prompt, validator, golden set, runner, first two published runs | A4–A8 |
| **GATE** | end wk 8 | If M3 is not green, no work starts on M5–M6. Slip is absorbed by dropping CRM scope, never evals. | |
| M4 AWS | 9–10 | Dockerfile, ECR, Terraform, App Runner, OIDC | A11, A12 |
| M5 Client | 11–12 | Student loop + teacher roster/assign | A13 |
| M6 CRM | 13–15 | Schools, lessons, attendance, contacts, terms | A14 |
| M7 Release | 16 | README, third eval run, tag v0.1.0 | Stop sentence |

## Working agreement

Claude writes scaffolding, config, CI, Terraform skeletons, test scaffolds, and reviews. Michael writes the engine, validator, authorisation rules, prompt, eval cases, engine spec, and decision log entries.
