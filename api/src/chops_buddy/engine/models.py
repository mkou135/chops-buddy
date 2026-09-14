"""Engine data types. Mirrors docs/ENGINE_SPEC.md §2, §4.1, §5, §6.

Scaffold: field names and ranges are fixed by the spec. Michael fills any
validators marked TODO. No logic lives here beyond validation.
"""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

Fragment = tuple[int, int]  # half-open [start, end) over unit indices


class Level(StrEnum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class InstrumentFamily(StrEnum):
    wind = "wind"
    brass = "brass"
    voice = "voice"
    strings = "strings"
    keyboard = "keyboard"
    percussion = "percussion"


class TargetKind(StrEnum):
    scale = "scale"
    technique = "technique"
    repertoire = "repertoire"


class Mode(StrEnum):
    working = "working"
    isolating = "isolating"
    chaining = "chaining"
    mastered = "mastered"


class Student(BaseModel):
    level: Level
    instrument_family: InstrumentFamily


class Target(BaseModel):
    id: str
    kind: TargetKind
    title: str
    target_tempo: int = Field(ge=20, le=300)
    units: list[str] = Field(min_length=1)  # E-15
    phrases: list[Fragment] | None = None  # E-14: non-overlapping, covering [0, n)
    start_tempo: int | None = Field(default=None, ge=20, le=300)  # E-13
    threshold_override: int | None = Field(default=None, ge=3, le=10)  # E-10

    @model_validator(mode="after")
    def _phrases_cover_units(self) -> "Target":
        # TODO(E-14): validate phrases are sorted, non-overlapping, and cover [0, len(units)).
        return self


class TargetState(BaseModel):
    """docs/ENGINE_SPEC.md §4.1."""

    mode: Mode
    tempo: int
    fragment: Fragment
    chain_base: Fragment
    chain_len: int = 0
    fails_here: int = 0
    mastery_streak: int = 0


class Prescription(BaseModel):
    id: str
    target_id: str
    mode: Mode
    fragment: Fragment
    tempo: int
    threshold: int
    minutes: int
    instruction: str


class LogEntry(BaseModel):
    """docs/ENGINE_SPEC.md §6."""

    prescription_id: str
    tempo_used: int = Field(ge=20, le=300)
    best_consecutive: int = Field(ge=0, le=50)
    break_unit: int | None = None
    felt_difficulty: int = Field(ge=1, le=5)
    free_text: str | None = Field(default=None, max_length=500)  # ignored by the engine


class Segment(BaseModel):
    kind: Literal["long_tones", "scale", "technique", "repertoire"]
    target_id: str | None  # None for long tones
    prescription: Prescription | None  # None for long tones
    minutes: int
    instruction: str


class SessionPlan(BaseModel):
    segments: list[Segment]
    deferred: list[str] = Field(default_factory=list)  # E-55: target ids dropped for time
    plan_hash: str  # E-70


class EngineError(Exception):
    """Raised for spec-defined rejections (E-21, E-56, E-60, E-61)."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
