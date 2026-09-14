"""The propose-then-validate path inside POST /me/sessions (DECISIONS #5, DoD A4)."""

import pytest
from httpx import AsyncClient

from chops_buddy.api import services
from chops_buddy.db.models import Profile, Student
from chops_buddy.llm.proposal import Proposal, ProposedSegment
from chops_buddy.llm.proposer import FakeProposer
from chops_buddy.settings import settings
from tests.api.conftest import TARGET_BODY, bearer


async def assign(client: AsyncClient, teacher: Profile, student: Student) -> str:
    r = await client.post(
        f"/teacher/students/{student.id}/targets", json=TARGET_BODY, headers=bearer(teacher.id)
    )
    return r.json()["id"]


async def test_llm_proposal_is_validated_and_recorded(
    client: AsyncClient, teacher: Profile, student: Student, monkeypatch: pytest.MonkeyPatch
) -> None:
    tid = await assign(client, teacher, student)
    settings.llm_api_key = "test-key"
    fake = FakeProposer(
        Proposal(
            segments=[
                ProposedSegment(target_id="long_tones", minutes=4),
                ProposedSegment(target_id=tid, minutes=16),
            ],
            rationale="student said the reed was fine",
            coaching_note="Steady and slow.",
        )
    )
    monkeypatch.setattr(services, "make_proposer", lambda: fake)
    try:
        assert student.profile_id is not None
        r = await client.post(
            "/me/sessions", json={"duration_minutes": 20}, headers=bearer(student.profile_id)
        )
    finally:
        settings.llm_api_key = None
    assert r.status_code == 201
    body = r.json()
    assert body["source"] == "llm"
    assert [s["minutes"] for s in body["plan"]["segments"]] == [4, 16]
    assert body["llm_report"] == {
        "violations": [],
        "repaired": False,
        "coaching_note": "Steady and slow.",
    }


async def test_illegal_proposal_is_repaired_and_reported(
    client: AsyncClient, teacher: Profile, student: Student, monkeypatch: pytest.MonkeyPatch
) -> None:
    tid = await assign(client, teacher, student)
    settings.llm_api_key = "test-key"
    fake = FakeProposer(
        Proposal(
            segments=[ProposedSegment(target_id=tid, minutes=20)],
            rationale="x",
            coaching_note="Keep your streak!",
        )
    )
    monkeypatch.setattr(services, "make_proposer", lambda: fake)
    try:
        assert student.profile_id is not None
        r = await client.post(
            "/me/sessions", json={"duration_minutes": 20}, headers=bearer(student.profile_id)
        )
    finally:
        settings.llm_api_key = None
    body = r.json()
    assert body["source"] == "llm"
    assert (
        set(body["llm_report"]["violations"])
        == {"long_tones_rule", "gamification_language", "minutes_sum"}
        or "long_tones_rule" in body["llm_report"]["violations"]
    )
    assert body["llm_report"]["repaired"] is True
    assert body["llm_report"]["coaching_note"] is None
    assert sum(s["minutes"] for s in body["plan"]["segments"]) == 20


async def test_model_error_falls_back_to_engine_source(
    client: AsyncClient, teacher: Profile, student: Student, monkeypatch: pytest.MonkeyPatch
) -> None:
    await assign(client, teacher, student)
    settings.llm_api_key = "test-key"
    monkeypatch.setattr(services, "make_proposer", lambda: FakeProposer(error=RuntimeError("down")))
    try:
        assert student.profile_id is not None
        r = await client.post(
            "/me/sessions", json={"duration_minutes": 10}, headers=bearer(student.profile_id)
        )
    finally:
        settings.llm_api_key = None
    assert r.status_code == 201
    assert r.json()["source"] == "engine"
    assert r.json()["llm_report"]["violations"] == ["model_error"]
