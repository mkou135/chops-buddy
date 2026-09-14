# Chops Buddy

A music practice and teaching platform for instrumental teachers and their students. The student side turns a teacher's assignments into a guided practice session, the way a programmed gym session guides a lifter. The teacher side is a small CRM for itinerant teachers working across several schools.

**Status: v0.1 in progress.** Scope and the finish line are fixed in [docs/DEFINITION_OF_DONE.md](docs/DEFINITION_OF_DONE.md). Every design choice is in [docs/DECISIONS.md](docs/DECISIONS.md).

## Why this exists

The pedagogy is the point. It is written down in [docs/pedagogy/](docs/pedagogy/) and encoded as a deterministic engine: repetition thresholds, slow-on-failure, fragment isolation, a tempo ladder, and backwards chaining. The engine works with no model present.

One narrow LLM task sits above it: read a student's practice log and propose the next session. The engine validates every proposal. That task is measured by a published eval suite whose results, including regressions, are committed to this repo.

## Architecture

```
web/    Next.js client (GitHub Pages)  ── Supabase Auth JWT ──▶  api/  FastAPI on AWS App Runner
                                                                    ├── engine/   pure Python, no I/O, no model
                                                                    ├── llm/      one prompt, structured output, validator
                                                                    ├── db/       SQLAlchemy 2 + Alembic → Supabase Postgres
                                                                    └── evals/    golden cases, runner, results/
infra/  Terraform for the AWS side
```

## Eval results

The model's one job is to propose the next session's minute allocation, deferrals, and wording; a deterministic validator checks every proposal against the methodology and repairs or rejects it. Fifty golden cases in `api/evals/cases/` grade the model's intent; results are appended to `api/evals/results/` and never edited. Regressions stay in the table.

<!-- evals:start -->
No runs yet.
<!-- evals:end -->

Run locally with an Anthropic key:

```bash
cd api && CB_LLM_API_KEY=... python -m evals --write
```

## Running locally

API:

```bash
cd api && python -m venv .venv && source .venv/bin/activate && pip install -e '.[dev]' && uvicorn chops_buddy.api.main:app --reload
```

Client:

```bash
cd web && npm install && npm run dev
```

## Related

- [Woodshed](https://github.com/mkou135/woodshed): the same engineering pattern (deterministic core, optional model layer, published spec, decision log) applied to jazz solo analysis.
