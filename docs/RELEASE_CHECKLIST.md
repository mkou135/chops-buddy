# v0.1.0 release checklist

Tick each acceptance criterion from `DEFINITION_OF_DONE.md` in the release PR with its evidence. The stop sentence is met only when every row is ticked.

| ID | Criterion | Evidence | Status |
|---|---|---|---|
| A1 | Engine imports only stdlib + pydantic; 100% branch coverage on the state machine | `tests/engine/test_boundary.py`; CI coverage: `engine/state.py 100%` | done |
| A2 | Every ENGINE_SPEC rule has a named test | `docs/ENGINE_SPEC.md` rule table; `pytest tests/engine` (41 tests, no xfail) | done |
| A3 | Byte-identical plan across 100 runs | `test_determinism::test_plan_is_byte_identical_across_100_runs` | done |
| A4 | API returns a valid session with the LLM key unset | `test_student::test_next_session_with_llm_absent_comes_from_engine` | done |
| A5 | Validator rejects each rule class, each with a fixture | `tests/llm/test_validator.py` (11 codes) | done |
| A6 | ≥50 golden cases, ≥5 per category, each with a note | `python -m evals --count` → 50; `test_runner::test_golden_set_has_fifty_cases_five_per_category_with_notes` | done |
| A7 | Runner exits non-zero on a >5-point drop | `test_runner::test_regression_gate_fails_on_five_point_drop`; `evals/__main__.py` exit 1 | done |
| A8 | ≥3 dated eval runs committed, README table regenerated, failures listed | `api/evals/results/` | **blocked: needs `ANTHROPIC_API_KEY` secret, then 3 runs (weekly job or manual dispatch)** |
| A9 | 401 without token, 403 across tenant, ≥6 named authorisation tests | `tests/api/test_auth.py`, `test_teacher.py`, `test_student.py`, `test_crm.py` | done |
| A10 | Migrations apply from empty in CI; seed runs <30 s | CI `api` job (postgres:16 service); `tests/db/test_seed.py` | done |
| A11 | Terraform plan clean on main; apply from CI produces the service | `deploy.yml` terraform job | **blocked: needs AWS bootstrap + `AWS_ROLE_ARN`, `TF_STATE_BUCKET`** |
| A12 | Live `/health` returns 200 with the commit SHA | `deploy.yml` release job polls App Runner | **blocked: as A11, plus `CB_DATABASE_URL_MIGRATIONS` and the three SSM values** |
| A13 | Student completes sign-in → session → log → history against the live API | screen recording linked in the release PR | **blocked: A12 + Pages enabled + `NEXT_PUBLIC_*` variables + Supabase project** |
| A14 | Teacher creates school, adds student, assigns, schedules lesson, marks attendance, adds contact, adds term | screen recording | **blocked: as A13** |
| A15 | DECISIONS.md ≥25 entries with who/what/reverses | `docs/DECISIONS.md` (31) | done |
| A16 | ENGINE_SPEC merged before first engine commit | PR #4 merged before PR #6 | done |
| A17 | Prototype code is the live client or removed; no "not yet wired" README | PR #12 | done |
| A18 | README shows architecture diagram and eval table above the fold | `README.md` | done (table fills at A8) |

## Release steps, in order

1. Set the repository secrets and variables listed in the blocked rows (see `infra/README.md`, `web/README.md`, and the M3 PR).
2. Push to `main` or run the `deploy` workflow; confirm the release job prints the App Runner URL and the SHA check passes (A11, A12).
3. Run the `pages` workflow; confirm the client loads at the Pages URL.
4. Run the `ci` workflow manually three times, or wait three weeks of the Sunday schedule, so `api/evals/results/` has three files. Regenerate the README table (`python evals/report.py`) if a run was local (A8).
5. Seed the live database if you want demo data: `CB_DATABASE_URL=<session pooler> python -m chops_buddy.seed` from `api/`.
6. Record the two walkthroughs (A13, A14) and link them.
7. Open the release PR titled `v0.1.0`, paste this table with every row ticked, merge, tag:
   ```bash
   git tag -a v0.1.0 -m "v0.1.0" && git push origin v0.1.0
   ```
