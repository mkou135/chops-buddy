"""ORM models. See docs/DATA_MODEL.md.

Engine-owned shapes are stored as JSONB snapshots (DECISIONS #16); the `to_engine`
helpers are the only translation layer.
"""

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from chops_buddy.engine.models import InstrumentFamily, Level, TargetKind
from chops_buddy.engine.models import Target as EngineTarget


class Base(DeclarativeBase):
    type_annotation_map = {dict[str, Any]: JSONB, list[Any]: JSONB}


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def _created_at() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


def _updated_at() -> Mapped[datetime]:
    return mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = (CheckConstraint("role in ('teacher', 'student')", name="profiles_role"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)  # auth.users.id
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()


class School(Base):
    __tablename__ = "schools"

    id: Mapped[uuid.UUID] = _uuid_pk()
    name: Mapped[str] = mapped_column(Text, nullable=False)
    suburb: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()


class SchoolMembership(Base):
    __tablename__ = "school_memberships"

    teacher_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True
    )
    school_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("schools.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = _created_at()


class Student(Base):
    __tablename__ = "students"
    __table_args__ = (
        CheckConstraint("level in ('beginner', 'intermediate', 'advanced')", name="students_level"),
        Index("students_teacher_active_idx", "teacher_id", "is_active"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False
    )
    school_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("schools.id", ondelete="SET NULL")
    )
    profile_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("profiles.id", ondelete="SET NULL"), unique=True
    )
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[Level] = mapped_column(String(16), nullable=False)
    instrument_family: Mapped[InstrumentFamily] = mapped_column(String(16), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()

    targets: Mapped[list["Target"]] = relationship(back_populates="student")


class Target(Base):
    __tablename__ = "targets"
    __table_args__ = (
        CheckConstraint("kind in ('scale', 'technique', 'repertoire')", name="targets_kind"),
        CheckConstraint("target_tempo between 20 and 300", name="targets_tempo_range"),
        CheckConstraint("jsonb_array_length(units) >= 1", name="targets_units_non_empty"),
        CheckConstraint(
            "threshold_override is null or threshold_override between 3 and 10",
            name="targets_threshold_range",
        ),
        Index("targets_student_active_position_idx", "student_id", "is_active", "position"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[TargetKind] = mapped_column(String(16), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    target_tempo: Mapped[int] = mapped_column(Integer, nullable=False)
    units: Mapped[list[Any]] = mapped_column(JSONB, nullable=False)
    phrases: Mapped[list[Any] | None] = mapped_column(JSONB)
    start_tempo: Mapped[int | None] = mapped_column(Integer)
    threshold_override: Mapped[int | None] = mapped_column(Integer)
    position: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()

    student: Mapped[Student] = relationship(back_populates="targets")
    state_row: Mapped["TargetStateRow | None"] = relationship(
        back_populates="target", cascade="all, delete-orphan", lazy="selectin"
    )

    def to_engine(self) -> EngineTarget:
        return EngineTarget(
            id=str(self.id),
            kind=TargetKind(self.kind),
            title=self.title,
            target_tempo=self.target_tempo,
            units=list(self.units),
            phrases=[(p[0], p[1]) for p in self.phrases] if self.phrases else None,
            start_tempo=self.start_tempo,
            threshold_override=self.threshold_override,
        )


class TargetStateRow(Base):
    __tablename__ = "target_states"

    target_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("targets.id", ondelete="CASCADE"), primary_key=True
    )
    state: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)  # engine TargetState
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    updated_at: Mapped[datetime] = _updated_at()

    target: Mapped[Target] = relationship(back_populates="state_row")


class PracticeSession(Base):
    __tablename__ = "practice_sessions"
    __table_args__ = (
        CheckConstraint("duration_minutes in (10, 20, 30)", name="sessions_duration"),
        CheckConstraint("source in ('engine', 'llm')", name="sessions_source"),
        Index("sessions_student_created_idx", "student_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    plan: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)  # engine SessionPlan
    plan_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str] = mapped_column(String(8), nullable=False, server_default=text("'engine'"))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    llm_report: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB
    )  # validator verdict when source is llm
    created_at: Mapped[datetime] = _created_at()

    prescriptions: Mapped[list["Prescription"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="Prescription.position"
    )


class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("practice_sessions.id", ondelete="CASCADE"), nullable=False
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("targets.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)  # engine Prescription
    created_at: Mapped[datetime] = _created_at()

    session: Mapped[PracticeSession] = relationship(back_populates="prescriptions")


class LogEntry(Base):
    __tablename__ = "log_entries"
    __table_args__ = (
        CheckConstraint("felt_difficulty between 1 and 5", name="log_entries_difficulty"),
        CheckConstraint("best_consecutive between 0 and 50", name="log_entries_best"),
        CheckConstraint("tempo_used between 20 and 300", name="log_entries_tempo"),
        Index("log_entries_student_created_idx", "student_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    prescription_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("prescriptions.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    tempo_used: Mapped[int] = mapped_column(Integer, nullable=False)
    best_consecutive: Mapped[int] = mapped_column(Integer, nullable=False)
    break_unit: Mapped[int | None] = mapped_column(Integer)
    felt_difficulty: Mapped[int] = mapped_column(Integer, nullable=False)
    free_text: Mapped[str | None] = mapped_column(String(500))
    state_after: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)  # engine TargetState
    created_at: Mapped[datetime] = _created_at()


# --- CRM (M6) ---------------------------------------------------------------------------


class Term(Base):
    __tablename__ = "terms"
    __table_args__ = (CheckConstraint("starts_on < ends_on", name="terms_dates_ordered"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    school_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    starts_on: Mapped[date] = mapped_column(Date, nullable=False)
    ends_on: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = _created_at()


class Lesson(Base):
    __tablename__ = "lessons"
    __table_args__ = (
        CheckConstraint(
            "status in ('scheduled', 'completed', 'cancelled', 'missed')", name="lessons_status"
        ),
        CheckConstraint("duration_minutes between 10 and 180", name="lessons_duration"),
        Index("lessons_teacher_scheduled_idx", "teacher_id", "scheduled_at"),
        Index("lessons_student_scheduled_idx", "student_id", "scheduled_at"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False
    )
    term_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("terms.id", ondelete="SET NULL"))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'scheduled'")
    )
    notes: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()

    attendance: Mapped["Attendance | None"] = relationship(
        back_populates="lesson", cascade="all, delete-orphan", lazy="selectin"
    )


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (
        CheckConstraint(
            "status in ('present', 'absent', 'late', 'cancelled')", name="attendance_status"
        ),
    )

    lesson_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = _updated_at()

    lesson: Mapped[Lesson] = relationship(back_populates="attendance")


class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = (Index("contacts_student_idx", "student_id"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    relationship_: Mapped[str] = mapped_column("relationship", Text, nullable=False)
    phone: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(Text)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[datetime] = _created_at()
