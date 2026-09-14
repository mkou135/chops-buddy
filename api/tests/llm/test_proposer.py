"""Prompt construction and the propose-then-validate path, with a fake model."""

from chops_buddy.engine.models import InstrumentFamily, Level, Student, Target, TargetKind
from chops_buddy.engine.state import initial_state
from chops_buddy.llm.proposal import Proposal, ProposedSegment
from chops_buddy.llm.proposer import FakeProposer, ProposalRequest, build_prompt, propose_session
from chops_buddy.llm.validator import LONG_TONES_ID

STUDENT = Student(level=Level.beginner, instrument_family=InstrumentFamily.wind)


def request() -> ProposalRequest:
    t = Target(
        id="r1", kind=TargetKind.repertoire, title="Minuet", target_tempo=100, units=list("abcd")
    )
    return ProposalRequest(
        student=STUDENT,
        targets=[(t, initial_state(t))],
        duration_minutes=20,
        recent_logs=[
            {
                "target_id": "r1",
                "tempo_used": 60,
                "best_consecutive": 2,
                "felt_difficulty": 5,
                "free_text": "my reed split",
            }
        ],
    )


def test_prompt_contains_state_logs_and_engine_default() -> None:
    system, user = build_prompt(request(), engine_default_minutes={LONG_TONES_ID: 3, "r1": 17})
    assert "Minuet" in user and "my reed split" in user
    assert '"r1": 17' in user  # engine default allocation shown
    assert "Do not mention points, streaks, badges" in system  # Designing for Motivation §1
    assert "minutes" in system and "deferred" in system


async def test_propose_session_validates_and_reports_source() -> None:
    fake = FakeProposer(
        Proposal(
            segments=[
                ProposedSegment(target_id=LONG_TONES_ID, minutes=3),
                ProposedSegment(target_id="r1", minutes=17),
            ],
            deferred=[],
            rationale="ok",
            coaching_note="Slow is fine.",
        )
    )
    outcome = await propose_session(request(), fake, lambda tid: f"p-{tid}")
    assert outcome.source == "llm" and outcome.report.violations == []
    assert outcome.plan.segments[1].minutes == 17


async def test_model_failure_falls_back_to_engine() -> None:
    outcome = await propose_session(
        request(), FakeProposer(error=RuntimeError("boom")), lambda tid: f"p-{tid}"
    )
    assert outcome.source == "engine"
    assert outcome.report.violations == ["model_error"]
