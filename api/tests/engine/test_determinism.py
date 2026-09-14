"""Tests for docs/ENGINE_SPEC.md E-03, E-70, E-71."""

from chops_buddy.engine.compose import compose, plan_hash
from chops_buddy.engine.models import (
    InstrumentFamily,
    Level,
    Mode,
    SessionPlan,
    Student,
    Target,
    TargetKind,
)
from chops_buddy.engine.state import initial_state

STUDENT = Student(level=Level.advanced, instrument_family=InstrumentFamily.brass)


def targets() -> list[tuple[Target, object]]:
    out: list[tuple[Target, object]] = []
    for i, kind in enumerate((TargetKind.scale, TargetKind.technique, TargetKind.repertoire)):
        t = Target(
            id=f"t{i}", kind=kind, title=f"T{i}", target_tempo=100 + 10 * i, units=list("abcdef")
        )
        s = initial_state(t)
        if i == 2:
            s = s.model_copy(update={"mode": Mode.isolating, "fragment": (1, 5), "tempo": 52})
        out.append((t, s))
    return out


def build(id_prefix: str = "p") -> SessionPlan:
    return compose(STUDENT, targets(), 20, lambda tid: f"{id_prefix}-{tid}")  # type: ignore[arg-type]


def test_plan_is_byte_identical_across_100_runs() -> None:
    first = build().model_dump_json()
    assert all(build().model_dump_json() == first for _ in range(99))


def test_plan_hash_excludes_ids_and_timestamps() -> None:
    a, b = build("p"), build("q")
    assert a.plan_hash == b.plan_hash
    assert a.plan_hash == plan_hash(a)
    assert len(a.plan_hash) == 64
    different = compose(STUDENT, targets(), 30, lambda tid: f"p-{tid}")  # type: ignore[arg-type]
    assert different.plan_hash != a.plan_hash


def test_equal_hash_means_equal_visible_plan() -> None:
    a, b = build("p"), build("q")
    visible = lambda p: [  # noqa: E731
        (s.kind, s.target_id, s.minutes, s.instruction, s.prescription and s.prescription.tempo)
        for s in p.segments
    ]
    assert a.plan_hash == b.plan_hash and visible(a) == visible(b)
