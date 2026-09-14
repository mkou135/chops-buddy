"""Prompt, model call, and the propose-then-validate path (DECISIONS #5).

The prompt is frozen text plus a JSON rendering of the inputs. `PROMPT_VERSION` is
the SHA of the system prompt and is recorded with every eval run.
"""

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

from chops_buddy.engine import compose as engine_compose
from chops_buddy.engine.models import SessionPlan, Student, Target, TargetState
from chops_buddy.llm.proposal import Proposal
from chops_buddy.llm.validator import LONG_TONES_ID, ValidationResult, validate

DEFAULT_MODEL = "claude-opus-5"

SYSTEM_PROMPT = """You plan one home practice session for an instrumental music student.

You are given the student's level and instrument family, each assigned target with the
engine's current state for it (mode, working tempo, fragment), the student's recent
practice log entries including their own words, the session length in minutes, and the
engine's default minute allocation.

You decide only three things:
1. minutes per target (and for long tones when present), summing exactly to the session length,
   with every scheduled segment at least 2 minutes;
2. which assigned targets to defer from this session, if any, giving each a reason in the rationale;
3. a one-paragraph rationale for the teacher and a one-sentence coaching note for the student.

You do not decide tempo, mode, fragment, or repetition threshold. The engine owns those
and they are shown for context only. Never invent targets. A target in isolating or
chaining mode must not be deferred. Do not mention points, streaks, badges, or rewards;
the student's reward is the music itself. Prefer the engine's default allocation unless
the log gives a concrete reason to change it (a broken reed, a passage that felt secure,
a target the student has not touched, fatigue mentioned in their words).
"""

PROMPT_VERSION = hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest()[:8]


@dataclass
class ProposalRequest:
    student: Student
    targets: list[tuple[Target, TargetState]]
    duration_minutes: int
    recent_logs: list[dict[str, Any]] = field(default_factory=list)  # pyright: ignore[reportUnknownVariableType]


def build_prompt(
    request: ProposalRequest, engine_default_minutes: dict[str, int]
) -> tuple[str, str]:
    payload = {
        "student": request.student.model_dump(mode="json"),
        "session_minutes": request.duration_minutes,
        "targets": [
            {**t.model_dump(mode="json"), "state": s.model_dump(mode="json")}
            for t, s in request.targets
        ],
        "recent_logs": request.recent_logs,
        "engine_default_minutes": engine_default_minutes,
    }
    user = "Plan the session for these inputs.\n\n" + json.dumps(payload, indent=1, sort_keys=True)
    return SYSTEM_PROMPT, user


class Proposer(Protocol):
    async def propose(self, system: str, user: str) -> Proposal: ...


class FakeProposer:
    """Returns a canned proposal, or raises. For tests and the eval runner's dry mode."""

    def __init__(self, proposal: Proposal | None = None, error: Exception | None = None) -> None:
        self._proposal = proposal
        self._error = error

    async def propose(self, system: str, user: str) -> Proposal:
        if self._error:
            raise self._error
        assert self._proposal is not None
        return self._proposal


class AnthropicProposer:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        import anthropic

        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    async def propose(self, system: str, user: str) -> Proposal:
        response = await self._client.messages.parse(
            model=self._model,
            max_tokens=4000,
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
            output_format=Proposal,
        )
        parsed = response.parsed_output
        if parsed is None:
            raise RuntimeError(f"no parsed output (stop_reason={response.stop_reason})")
        return parsed


@dataclass
class ProposalOutcome:
    plan: SessionPlan
    source: str  # "llm" or "engine"
    report: ValidationResult
    proposal: Proposal | None


def engine_default_minutes(request: ProposalRequest, pid: Callable[[str], str]) -> dict[str, int]:
    plan = engine_compose.compose(request.student, request.targets, request.duration_minutes, pid)
    return {s.target_id or LONG_TONES_ID: s.minutes for s in plan.segments}


async def propose_session(
    request: ProposalRequest, proposer: Proposer, prescription_id: Callable[[str], str]
) -> ProposalOutcome:
    """Ask the model, validate, and return a plan. Any model failure yields the engine plan."""
    defaults = engine_default_minutes(request, prescription_id)
    system, user = build_prompt(request, defaults)
    try:
        proposal = await proposer.propose(system, user)
    except Exception:  # noqa: BLE001 - the whole point is that the engine never depends on the model
        plan = engine_compose.compose(
            request.student, request.targets, request.duration_minutes, prescription_id
        )
        return ProposalOutcome(
            plan=plan,
            source="engine",
            report=ValidationResult(plan=plan, violations=["model_error"], repaired=True),
            proposal=None,
        )
    report = validate(
        request.student, request.targets, request.duration_minutes, proposal, prescription_id
    )
    return ProposalOutcome(plan=report.plan, source="llm", report=report, proposal=proposal)
