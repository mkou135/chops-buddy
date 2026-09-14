# Decision log

Append-only. Each entry records what was decided, who decided, and what would reverse it. Never edit an old entry; add a new one that supersedes it.

| # | Date | Decision | Made by | Would reverse it |
|---|---|---|---|---|
| 1 | 2026-09-14 | This repo is the public home of the platform. The private `cadence` repo stays private and untouched; its ideas are ported, its code is not. | Michael | Deciding to open-source `cadence` itself |
| 2 | 2026-09-14 | Both student and teacher roles are in v0.1. | Michael, against advice to ship student-only | Missing milestone M3 by more than 2 weeks |
| 3 | 2026-09-14 | Full CRM (schools, lessons, notes, attendance, parent contacts, terms) is in v0.1, sequenced last so it cannot starve the engine or the evals. | Michael, against advice | Same trigger as #2: CRM drops to v0.2, v0.1 still ships |
| 4 | 2026-09-14 | Finish line is 16 weeks at ~6 h/week. | Michael | — |
| 5 | 2026-09-14 | The LLM proposes a session; a deterministic engine and validator decide. The engine must always produce a legal session with no model present. | Michael | Evals showing the validator rejects >50% of proposals over a full run |
| 6 | 2026-09-14 | A practice log entry is student self-report per target. No microphone, no audio. | Michael | — |
| 7 | 2026-09-14 | Hosting: FastAPI container on AWS App Runner; Supabase Postgres and Supabase Auth; Terraform for the AWS side. Chosen after two reversals in one session and recorded as final. | Michael | An App Runner limitation that requires VPC-only resources → ECS Fargate |
| 8 | 2026-09-14 | Backend defaults: SQLAlchemy 2 async + Alembic, Pydantic v2, pytest, ruff, pyright, GitHub Actions, OIDC to AWS with no long-lived keys. | Claude proposed, Michael approved | — |
| 9 | 2026-09-14 | Authorisation lives in the FastAPI service layer, not Supabase RLS. The API connects as one database role. RLS may be enabled as defence in depth but is not the tested enforcement point. | Claude proposed, Michael approved | Deciding the client should ever talk to Postgres directly |
| 10 | 2026-09-14 | Working agreement: Claude writes scaffolding, config, CI, Terraform skeletons, test scaffolds, and reviews. Michael writes the engine, validator, authorisation rules, prompt, eval cases, engine spec, and decision log entries. | Michael | — |
| 11 | 2026-09-14 | Reuse the existing public `chops-buddy` repo rather than create a new one. History is kept; the prototype README banner ("data layer not yet wired") is removed in M0. | Michael | — |
| 12 | 2026-09-14 | The existing Next.js 14 prototype becomes the thin client (supersedes the Vite/React default in #8). It is static-exported to GitHub Pages to keep Vercel out of the stack; Vercel is the fallback if export blocks a needed route. | Michael | Static export proving unworkable for the dynamic student route |
| 13 | 2026-09-14 | Monorepo layout: `web/` (Next.js), `api/` (Python service including `engine/`, `llm/`, `db/`, `api/`, `evals/`), `infra/` (Terraform), `docs/`. | Claude proposed, Michael approved | — |
| 14 | 2026-09-14 | Claude drafted the full ENGINE_SPEC (rules E-01 to E-71) at Michael's request, making all parameter choices. This supersedes the "Michael writes the spec" clause of #10; Michael owns the spec by review and edits rules in the doc before code. The rest of #10 stands. | Michael | — |
| 15 | 2026-09-14 | Claude implements the engine rules test-first, at Michael's request. This supersedes the "Michael writes the engine" clause of #10. Michael reviews each PR against the spec; the validator, prompt, and eval cases remain his unless a later entry says otherwise. | Michael | — |
| 16 | 2026-09-14 | Engine-owned shapes (TargetState, Prescription, SessionPlan, LogEntry) are stored as JSONB snapshots of the engine's pydantic models, not as columns. The engine is the schema for them; the database never reinterprets them. | Claude proposed, Michael to confirm in PR review | Needing to query inside those shapes in SQL for a product feature |
| 17 | 2026-09-14 | Local tests use an embedded Postgres 16 installed via pip (`pgserver`); CI uses a Postgres service container (DoD A10). No Docker or system Postgres is required on the dev machine. | Claude proposed | `pgserver` losing macOS or Linux wheels |
