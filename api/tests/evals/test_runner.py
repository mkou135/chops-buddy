"""Eval runner: case loading, deterministic grading, results, regression gate (A6-A8)."""

import json
from pathlib import Path

import pytest
from evals.runner import (
    CASES_DIR,
    Case,
    grade,
    load_cases,
    regression_gate,
    run,
    summarise,
    write_results,
)

from chops_buddy.llm.proposal import Proposal, ProposedSegment
from chops_buddy.llm.proposer import FakeProposer

CATEGORIES = {
    "happy_path",
    "stalled_student",
    "ambiguous_free_text",
    "contradictory_self_report",
    "level_boundaries",
    "indivisible_units",
    "first_session",
    "teacher_override",
}


def test_golden_set_has_fifty_cases_five_per_category_with_notes() -> None:
    cases = load_cases(CASES_DIR)
    assert len(cases) >= 50
    by_cat: dict[str, int] = {}
    for c in cases:
        by_cat[c.category] = by_cat.get(c.category, 0) + 1
        assert c.note.strip(), f"{c.slug} has no author note"
        assert c.assertions, f"{c.slug} has no assertions"
    assert set(by_cat) == CATEGORIES
    assert all(n >= 5 for n in by_cat.values()), by_cat


def test_every_case_input_is_valid_for_the_engine() -> None:
    from chops_buddy.engine.compose import compose

    for c in load_cases(CASES_DIR):
        plan = compose(c.student, c.pairs(), c.duration_minutes, lambda t: f"p-{t}")
        assert plan.segments, c.slug


def test_grade_checks_each_assertion_type(tmp_path: Path) -> None:
    case = Case(
        slug="x",
        category="happy_path",
        note="n",
        input={
            "student": {"level": "beginner", "instrument_family": "keyboard"},
            "targets": [
                {
                    "id": "s1",
                    "kind": "scale",
                    "title": "G major",
                    "target_tempo": 80,
                    "units": ["1", "2"],
                },
                {
                    "id": "r1",
                    "kind": "repertoire",
                    "title": "Song",
                    "target_tempo": 100,
                    "units": ["a", "b", "c"],
                    "state": {
                        "mode": "isolating",
                        "tempo": 40,
                        "fragment": [1, 3],
                        "chain_base": [0, 3],
                    },
                },
            ],
            "duration_minutes": 10,
            "recent_logs": [],
        },
        assertions=[
            {"type": "legal"},
            {"type": "does_not_defer", "target_id": "r1"},
            {"type": "minutes_at_least", "target_id": "r1", "minutes": 5},
            {"type": "mentions_none_of", "words": ["ghost"]},
        ],
    )
    good = Proposal(
        segments=[
            ProposedSegment(target_id="s1", minutes=4),
            ProposedSegment(target_id="r1", minutes=6),
        ],
        deferred=[],
        rationale="focus the isolated bar",
        coaching_note="Small and slow.",
    )
    result = grade(case, good)
    assert result.passed and all(a.passed for a in result.assertions)
    bad = good.model_copy(
        update={
            "segments": [ProposedSegment(target_id="s1", minutes=10)],
            "deferred": ["r1"],
            "rationale": "ghost",
        }
    )
    result = grade(case, bad)
    assert not result.passed
    assert [a.type for a in result.assertions if not a.passed] == [
        "legal",
        "does_not_defer",
        "minutes_at_least",
        "mentions_none_of",
    ]


async def test_run_writes_results_and_summary(tmp_path: Path) -> None:
    cases = load_cases(CASES_DIR)[:3]
    fake = FakeProposer(Proposal(segments=[], deferred=[], rationale="", coaching_note=""))
    results = await run(cases, fake, model="fake", prompt_sha="deadbeef")
    summary = summarise(results)
    assert summary["total"] == 3 and 0.0 <= summary["pass_rate"] <= 1.0
    assert "legality_rate" in summary and "repair_rate" in summary and "by_category" in summary
    path = write_results(tmp_path, results, summary, model="fake", prompt_sha="deadbeef")
    data = json.loads(path.read_text())
    assert data["summary"]["total"] == 3 and len(data["cases"]) == 3
    assert all("passed" in c and "assertions" in c for c in data["cases"])


def test_regression_gate_fails_on_five_point_drop(tmp_path: Path) -> None:
    (tmp_path / "2026-09-01-fake-aaaa.json").write_text(
        json.dumps({"summary": {"pass_rate": 0.90}})
    )
    assert regression_gate(tmp_path, current_pass_rate=0.86) is True
    assert regression_gate(tmp_path, current_pass_rate=0.84) is False
    assert regression_gate(tmp_path / "empty", current_pass_rate=0.1) is True  # no baseline


def test_runner_cli_reports_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    from evals.__main__ import main

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("CB_LLM_API_KEY", raising=False)
    assert main([]) == 3
