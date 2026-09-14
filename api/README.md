# api

FastAPI service, deterministic practice engine, LLM layer, and eval suite.

## Milestone M1 workflow (engine)

Every rule in `docs/ENGINE_SPEC.md` has a test in `tests/engine/` with the name the spec table gives it. Each starts as `@pytest.mark.xfail(strict=True)`.

To implement a rule:

1. Write the real test body against the fixtures in `tests/engine/conftest.py`.
2. Remove the `xfail` marker. The test now fails.
3. Implement the rule in `src/chops_buddy/engine/` until it passes.
4. Commit with the rule id in the message, e.g. `engine: E-30 tempo ladder climbs one rung`.

`strict=True` means CI turns red if a rule starts passing while still marked, so markers cannot be forgotten. DoD A2 is met when no `xfail` markers remain in `tests/engine/`.

## Commands

```bash
python3.11 -m venv .venv && source .venv/bin/activate && pip install -e '.[dev]'
ruff check . && ruff format --check . && pyright && pytest --cov
python -m evals --count
```
