"""Golden-case eval runner. Grading is deterministic; no judge model (DoD: evals)."""

import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from chops_buddy.engine.models import Student, Target, TargetState
from chops_buddy.engine.state import initial_state
from chops_buddy.llm.proposal import Proposal
from chops_buddy.llm.proposer import ProposalRequest, Proposer, propose_session
from chops_buddy.llm.validator import ValidationResult

EVALS_DIR = Path(__file__).parent
CASES_DIR = EVALS_DIR / "cases"
RESULTS_DIR = EVALS_DIR / "results"
REGRESSION_TOLERANCE = 0.05  # A7


@dataclass
class Case:
    slug: str
    category: str
    note: str
    input: dict[str, Any]
    assertions: list[dict[str, Any]]

    @property
    def student(self) -> Student:
        return Student.model_validate(self.input["student"])

    @property
    def duration_minutes(self) -> int:
        return int(self.input["duration_minutes"])

    def pairs(self) -> list[tuple[Target, TargetState]]:
        out: list[tuple[Target, TargetState]] = []
        for raw in self.input["targets"]:
            state_raw = raw.get("state")
            target = Target.model_validate({k: v for k, v in raw.items() if k != "state"})
            state = initial_state(target)
            if state_raw:
                state = state.model_copy(
                    update=TargetState.model_validate(
                        {**state.model_dump(), **state_raw}
                    ).model_dump()
                )
            out.append((target, state))
        return out

    def request(self) -> ProposalRequest:
        return ProposalRequest(
            student=self.student,
            targets=self.pairs(),
            duration_minutes=self.duration_minutes,
            recent_logs=list(self.input.get("recent_logs", [])),
        )


def load_cases(cases_dir: Path) -> list[Case]:
    cases: list[Case] = []
    for path in sorted(cases_dir.glob("*/*.json")):
        raw = json.loads(path.read_text())
        cases.append(
            Case(
                slug=path.stem,
                category=path.parent.name,
                note=raw.get("note", ""),
                input=raw["input"],
                assertions=raw.get("assertions", []),
            )
        )
    return cases


@dataclass
class AssertionResult:
    type: str
    passed: bool
    detail: str = ""


@dataclass
class CaseResult:
    slug: str
    category: str
    passed: bool
    violations: list[str]
    repaired: bool
    assertions: list[AssertionResult] = field(default_factory=list)
    source: str = "llm"


def _check(
    assertion: dict[str, Any], report: ValidationResult, proposal: Proposal | None, engine_hash: str
) -> AssertionResult:
    """Intent assertions (defer / minutes) grade the *proposal*; `legal` grades the validator's
    verdict on it; `agrees_with_engine` grades the plan the student would actually receive."""
    kind = assertion["type"]
    plan = report.plan
    proposed = {seg.target_id: seg.minutes for seg in proposal.segments} if proposal else {}
    proposed_deferred = list(proposal.deferred) if proposal else []
    if kind == "legal":
        return AssertionResult(kind, report.legal, ",".join(report.violations))
    if kind == "does_not_defer":
        tid = assertion["target_id"]
        ok = tid in proposed and tid not in proposed_deferred
        return AssertionResult(
            kind, ok, f"{tid} proposed={tid in proposed} deferred={tid in proposed_deferred}"
        )
    if kind == "defers":
        tid = assertion["target_id"]
        return AssertionResult(kind, tid in proposed_deferred, f"deferred={proposed_deferred}")
    if kind == "minutes_at_least":
        tid, want = assertion["target_id"], int(assertion["minutes"])
        got = proposed.get(tid, 0)
        return AssertionResult(kind, got >= want, f"{tid}: {got} >= {want}")
    if kind == "minutes_at_most":
        tid, want = assertion["target_id"], int(assertion["minutes"])
        got = proposed.get(tid, 0)
        return AssertionResult(kind, got <= want, f"{tid}: {got} <= {want}")
    if kind == "agrees_with_engine":
        return AssertionResult(kind, plan.plan_hash == engine_hash, "plan hash vs engine")
    if kind == "mentions_none_of":
        text = ((proposal.rationale + " " + proposal.coaching_note) if proposal else "").lower()
        hits = [w for w in assertion["words"] if re.search(rf"\b{re.escape(w.lower())}\b", text)]
        return AssertionResult(kind, not hits, f"hits={hits}")
    if kind == "rationale_mentions":
        text = (proposal.rationale if proposal else "").lower()
        missing = [w for w in assertion["words"] if w.lower() not in text]
        return AssertionResult(kind, not missing, f"missing={missing}")
    return AssertionResult(kind, False, "unknown assertion type")


def grade(case: Case, proposal: Proposal) -> CaseResult:
    from chops_buddy.engine.compose import compose
    from chops_buddy.llm.validator import validate

    pid = lambda tid: f"p-{tid}"  # noqa: E731
    pairs = case.pairs()
    report = validate(case.student, pairs, case.duration_minutes, proposal, pid)
    engine_hash = compose(case.student, pairs, case.duration_minutes, pid).plan_hash
    results = [_check(a, report, proposal, engine_hash) for a in case.assertions]
    return CaseResult(
        slug=case.slug,
        category=case.category,
        passed=all(r.passed for r in results),
        violations=report.violations,
        repaired=report.repaired,
        assertions=results,
    )


async def run(
    cases: list[Case], proposer: Proposer, *, model: str, prompt_sha: str
) -> list[CaseResult]:
    results: list[CaseResult] = []
    for case in cases:
        outcome = await propose_session(case.request(), proposer, lambda tid: f"p-{tid}")
        if outcome.proposal is None:
            results.append(
                CaseResult(
                    case.slug, case.category, False, ["model_error"], True, [], source="engine"
                )
            )
            continue
        results.append(grade(case, outcome.proposal))
    return results


def summarise(results: list[CaseResult]) -> dict[str, Any]:
    total = len(results)
    by_cat: dict[str, dict[str, int]] = {}
    for r in results:
        c = by_cat.setdefault(r.category, {"total": 0, "passed": 0})
        c["total"] += 1
        c["passed"] += int(r.passed)
    return {
        "total": total,
        "passed": sum(r.passed for r in results),
        "pass_rate": (sum(r.passed for r in results) / total) if total else 0.0,
        "legality_rate": (sum(not r.violations for r in results) / total) if total else 0.0,
        "repair_rate": (sum(r.repaired for r in results) / total) if total else 0.0,
        "by_category": {k: {**v, "pass_rate": v["passed"] / v["total"]} for k, v in by_cat.items()},
        "failing": [r.slug for r in results if not r.passed],
    }


def write_results(
    results_dir: Path,
    results: list[CaseResult],
    summary: dict[str, Any],
    *,
    model: str,
    prompt_sha: str,
) -> Path:
    results_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y-%m-%d")
    path = results_dir / f"{stamp}-{model}-{prompt_sha}.json"
    payload = {
        "run_at": datetime.now(UTC).isoformat(),
        "model": model,
        "prompt_sha": prompt_sha,
        "summary": summary,
        "cases": [
            {
                "slug": r.slug,
                "category": r.category,
                "passed": r.passed,
                "violations": r.violations,
                "repaired": r.repaired,
                "source": r.source,
                "assertions": [
                    {"type": a.type, "passed": a.passed, "detail": a.detail} for a in r.assertions
                ],
            }
            for r in results
        ],
    }
    path.write_text(json.dumps(payload, indent=1) + "\n")
    return path


def latest_pass_rate(results_dir: Path) -> float | None:
    files = sorted(results_dir.glob("*.json")) if results_dir.exists() else []
    if not files:
        return None
    return float(json.loads(files[-1].read_text())["summary"]["pass_rate"])


def regression_gate(results_dir: Path, current_pass_rate: float) -> bool:
    """A7: False when the pass rate dropped more than the tolerance versus the last run."""
    baseline = latest_pass_rate(results_dir)
    if baseline is None:
        return True
    return current_pass_rate >= baseline - REGRESSION_TOLERANCE
