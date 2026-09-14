"""Tests for docs/ENGINE_SPEC.md §4.2."""

import pytest

from chops_buddy.engine.models import EngineError, Level, Target
from chops_buddy.engine.state import apply, initial_state, is_pass
from tests.engine.conftest import entry
from tests.engine.helpers import prescription_for

LEVEL = Level.intermediate  # threshold 5


def test_pass_requires_tempo_and_threshold(walkthrough_target: Target) -> None:
    state = initial_state(walkthrough_target)  # tempo 72
    p = prescription_for(state, walkthrough_target, LEVEL)
    assert is_pass(entry("p", tempo_used=72, best=5), p)
    assert is_pass(entry("p", tempo_used=80, best=6), p)
    assert not is_pass(entry("p", tempo_used=72, best=4), p)
    assert not is_pass(entry("p", tempo_used=68, best=5), p)  # slower than prescribed
    # Free text and felt difficulty do not affect the judgement.
    assert is_pass(entry("p", tempo_used=72, best=5, difficulty=5), p)


def test_stale_prescription_rejected(walkthrough_target: Target) -> None:
    state = initial_state(walkthrough_target)
    stale = prescription_for(state, walkthrough_target, LEVEL, pid="old")
    stale = stale.model_copy(update={"tempo": 60})  # no longer matches the state
    with pytest.raises(EngineError) as exc:
        apply(state, walkthrough_target, LEVEL, stale, entry("old", tempo_used=60, best=5))
    assert exc.value.code == "stale_prescription"
