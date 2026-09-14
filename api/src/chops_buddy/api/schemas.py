"""Request and response bodies. Engine shapes are reused directly where they fit."""

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from chops_buddy.engine.models import (
    Fragment,
    InstrumentFamily,
    Level,
    SessionPlan,
    TargetKind,
    TargetState,
)


class ProfileOut(BaseModel):
    id: uuid.UUID
    role: str
    display_name: str


class ProfileCreate(BaseModel):
    role: Literal["teacher", "student"]
    display_name: str = Field(min_length=1, max_length=120)


class StudentCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    level: Level
    instrument_family: InstrumentFamily
    school_id: uuid.UUID | None = None


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    teacher_id: uuid.UUID
    school_id: uuid.UUID | None
    display_name: str
    level: Level
    instrument_family: InstrumentFamily
    is_active: bool


class TargetCreate(BaseModel):
    kind: TargetKind
    title: str = Field(min_length=1, max_length=200)
    target_tempo: int = Field(ge=20, le=300)
    units: list[str] = Field(min_length=1)
    phrases: list[Fragment] | None = None
    start_tempo: int | None = Field(default=None, ge=20, le=300)
    threshold_override: int | None = Field(default=None, ge=3, le=10)


class TargetOut(BaseModel):
    id: uuid.UUID
    kind: TargetKind
    title: str
    target_tempo: int
    units: list[str]
    phrases: list[Fragment] | None
    start_tempo: int | None
    threshold_override: int | None
    position: int
    is_active: bool
    state: TargetState


class StudentDetail(StudentOut):
    targets: list[TargetOut]


class SessionCreate(BaseModel):
    duration_minutes: Literal[10, 20, 30]


class LogCreate(BaseModel):
    prescription_id: uuid.UUID
    tempo_used: int = Field(ge=20, le=300)
    best_consecutive: int = Field(ge=0, le=50)
    break_unit: int | None = None
    felt_difficulty: int = Field(ge=1, le=5)
    free_text: str | None = Field(default=None, max_length=500)


class LogOut(BaseModel):
    id: uuid.UUID
    prescription_id: uuid.UUID
    tempo_used: int
    best_consecutive: int
    break_unit: int | None
    felt_difficulty: int
    free_text: str | None
    state_after: TargetState
    created_at: datetime


class SessionOut(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    duration_minutes: int
    source: str
    plan: SessionPlan
    created_at: datetime
    completed_at: datetime | None
    llm_report: dict[str, Any] | None = None
    logs: list[LogOut] = []


def plan_from_row(plan: dict[str, Any]) -> SessionPlan:
    return SessionPlan.model_validate(plan)
