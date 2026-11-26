"""ORM models for the SMIT research database.

Identifying contact information (email) lives ONLY in ``participant_contacts``;
all experimental tables reference participants by their pseudonymous
``participant_id``.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from ..db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UTCDateTime(TypeDecorator):
    """Timezone-aware UTC datetimes on every backend.

    SQLite does not store time zones, so values came back "naive" and the dashboard
    showed UTC times as if they were local time (5½ h early in India). Values are
    stored as UTC and always returned with tzinfo=UTC.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


SESSION_TYPES = ("main", "pilot")
PARTICIPANT_STATUSES = ("active", "withdrawn", "excluded")
COMPLETION_STATUSES = ("registered", "in_progress", "completed", "incomplete", "withdrawn", "abandoned")
CONDITIONS = ("A", "B", "C")
CONDITION_LABELS = {"A": "Control", "B": "Numerical interference", "C": "Visual interference"}
CONDITION_ORDERS = ("ABC", "ACB", "BAC", "BCA", "CAB", "CBA")


class Participant(Base):
    __tablename__ = "participants"
    __table_args__ = (
        CheckConstraint("age IS NULL OR (age >= 18 AND age <= 120)", name="ck_participant_age"),
        CheckConstraint("participant_type IN ('main','pilot')", name="ck_participant_type"),
        CheckConstraint("status IN ('active','withdrawn','excluded')", name="ck_participant_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    participant_id: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(40), nullable=True)
    academic_course: Mapped[str | None] = mapped_column(String(120), nullable=True)
    consent_status: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_timestamp: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    participant_type: Mapped[str] = mapped_column(String(10), default="main")
    status: Mapped[str] = mapped_column(String(20), default="active")
    status_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_source: Mapped[str] = mapped_column(String(20), default="app")  # app | import
    import_batch_id: Mapped[int | None] = mapped_column(ForeignKey("import_batches.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)

    contact: Mapped[ParticipantContact | None] = relationship(
        back_populates="participant", cascade="all, delete-orphan", uselist=False
    )
    sessions: Mapped[list[ExperimentSession]] = relationship(
        back_populates="participant", cascade="all, delete-orphan"
    )
    imported_summary: Mapped[ImportedParticipantSummary | None] = relationship(
        back_populates="participant", cascade="all, delete-orphan", uselist=False
    )


class ParticipantContact(Base):
    """CONFIDENTIAL identifying information, stored separately from research data."""

    __tablename__ = "participant_contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    participant_id: Mapped[str] = mapped_column(
        ForeignKey("participants.participant_id", ondelete="CASCADE"), unique=True
    )
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    email_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)

    participant: Mapped[Participant] = relationship(back_populates="contact")


class ExperimentConfigVersion(Base):
    __tablename__ = "experiment_configs"
    __table_args__ = (CheckConstraint("status IN ('draft','locked','retired')", name="ck_config_status"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version_number: Mapped[int] = mapped_column(Integer, unique=True)
    name: Mapped[str] = mapped_column(String(200))
    config_json: Mapped[dict] = mapped_column(JSON)
    config_hash: Mapped[str] = mapped_column(String(64))
    experiment_version: Mapped[str] = mapped_column(String(64), unique=True)
    status: Mapped[str] = mapped_column(String(10), default="draft")
    is_active_main: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("experiment_configs.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    lock_justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    locked_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)


class ExperimentSession(Base):
    __tablename__ = "experiment_sessions"
    __table_args__ = (
        CheckConstraint("session_type IN ('main','pilot')", name="ck_session_type"),
        CheckConstraint(
            "completion_status IN ('registered','in_progress','completed','incomplete','withdrawn','abandoned')",
            name="ck_completion_status",
        ),
        CheckConstraint("condition_order IN ('ABC','ACB','BAC','BCA','CAB','CBA')", name="ck_condition_order"),
    )

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    participant_id: Mapped[str] = mapped_column(
        ForeignKey("participants.participant_id", ondelete="CASCADE"), index=True
    )
    config_id: Mapped[int | None] = mapped_column(ForeignKey("experiment_configs.id"), nullable=True)
    experiment_version: Mapped[str] = mapped_column(String(64))
    session_type: Mapped[str] = mapped_column(String(10), default="main")
    condition_order: Mapped[str] = mapped_column(String(3))
    random_seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    trial_plan: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    device_information: Mapped[str | None] = mapped_column(Text, nullable=True)
    browser_information: Mapped[str | None] = mapped_column(Text, nullable=True)
    screen_information: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_refresh_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    start_time: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    completion_time: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    completion_status: Mapped[str] = mapped_column(String(20), default="registered")
    token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    practice_attempts: Mapped[int] = mapped_column(Integer, default=0)
    interruptions: Mapped[int] = mapped_column(Integer, default=0)
    fullscreen_exits: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_source: Mapped[str] = mapped_column(String(20), default="app")
    import_batch_id: Mapped[int | None] = mapped_column(ForeignKey("import_batches.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    last_activity: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)

    participant: Mapped[Participant] = relationship(back_populates="sessions")
    trials: Mapped[list[Trial]] = relationship(back_populates="session", cascade="all, delete-orphan")


class Trial(Base):
    __tablename__ = "trials"
    __table_args__ = (
        UniqueConstraint("session_id", "practice_trial", "practice_attempt", "trial_number", name="uq_trial_key"),
        CheckConstraint("condition IN ('A','B','C')", name="ck_trial_condition"),
        CheckConstraint("correct_answer IN ('same','different')", name="ck_trial_correct_answer"),
        CheckConstraint(
            "participant_response IS NULL OR participant_response IN ('same','different')",
            name="ck_trial_response",
        ),
        CheckConstraint("reaction_time_ms IS NULL OR reaction_time_ms >= 0", name="ck_trial_rt"),
        CheckConstraint("timing_quality_flag IN ('ok','warning','invalid')", name="ck_timing_flag"),
        CheckConstraint("exclusion_status IN ('included','excluded')", name="ck_exclusion_status"),
    )

    trial_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("experiment_sessions.session_id", ondelete="CASCADE"), index=True
    )
    participant_id: Mapped[str] = mapped_column(String(40), index=True)
    trial_number: Mapped[int] = mapped_column(Integer)
    block_number: Mapped[int] = mapped_column(Integer)
    condition: Mapped[str] = mapped_column(String(1))
    practice_trial: Mapped[bool] = mapped_column(Boolean, default=False)
    practice_attempt: Mapped[int] = mapped_column(Integer, default=0)
    original_pattern: Mapped[str] = mapped_column(String(64))
    recognition_pattern: Mapped[str] = mapped_column(String(64))
    correct_answer: Mapped[str] = mapped_column(String(10))
    participant_response: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    reaction_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    response_timeout: Mapped[bool] = mapped_column(Boolean, default=False)
    premature_keypresses: Mapped[int] = mapped_column(Integer, default=0)
    interference_type: Mapped[str] = mapped_column(String(20), default="none")
    interference_stimulus: Mapped[str | None] = mapped_column(String(120), nullable=True)
    interference_correct_answer: Mapped[str | None] = mapped_column(String(10), nullable=True)
    interference_response: Mapped[str | None] = mapped_column(String(10), nullable=True)
    interference_accuracy: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    interference_reaction_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    planned_fixation_duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_fixation_duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    planned_stimulus_duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    measured_stimulus_duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    planned_interference_duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    measured_interference_duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    planned_retention_duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    measured_retention_duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    planned_iti_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    inter_trial_interval_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    refresh_rate_hz: Mapped[float | None] = mapped_column(Float, nullable=True)
    dropped_frames: Mapped[int | None] = mapped_column(Integer, nullable=True)
    focus_loss: Mapped[bool] = mapped_column(Boolean, default=False)
    timing_quality_flag: Mapped[str] = mapped_column(String(10), default="ok")
    timing_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    exclusion_status: Mapped[str] = mapped_column(String(10), default="included")
    exclusion_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_timestamps: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)

    session: Mapped[ExperimentSession] = relationship(back_populates="trials")


class ImportedParticipantSummary(Base):
    """Participant-level metrics imported WITHOUT trial-level data (reduced analyses only)."""

    __tablename__ = "imported_participant_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    participant_id: Mapped[str] = mapped_column(
        ForeignKey("participants.participant_id", ondelete="CASCADE"), unique=True
    )
    experiment_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    condition_order: Mapped[str | None] = mapped_column(String(3), nullable=True)
    accuracy_a: Mapped[float] = mapped_column(Float)
    accuracy_b: Mapped[float] = mapped_column(Float)
    accuracy_c: Mapped[float] = mapped_column(Float)
    rt_a: Mapped[float | None] = mapped_column(Float, nullable=True)
    rt_b: Mapped[float | None] = mapped_column(Float, nullable=True)
    rt_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    timeout_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    secondary_accuracy_b: Mapped[float | None] = mapped_column(Float, nullable=True)
    secondary_accuracy_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    import_batch_id: Mapped[int | None] = mapped_column(ForeignKey("import_batches.id"), nullable=True)

    participant: Mapped[Participant] = relationship(back_populates="imported_summary")


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_names: Mapped[str] = mapped_column(Text)
    file_sha256: Mapped[str] = mapped_column(String(64), index=True)
    file_format: Mapped[str] = mapped_column(String(20))
    import_kind: Mapped[str] = mapped_column(String(20))  # full | summary
    status: Mapped[str] = mapped_column(String(20))  # validated | invalid | committed | cancelled
    validation_report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    staged_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    n_participants: Mapped[int] = mapped_column(Integer, default=0)
    n_sessions: Mapped[int] = mapped_column(Integer, default=0)
    n_trials: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    committed_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, index=True)
    actor: Mapped[str] = mapped_column(String(40))
    action: Mapped[str] = mapped_column(String(80), index=True)
    entity_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="completed")
    dataset_hash: Mapped[str] = mapped_column(String(64))
    n_participants_included: Mapped[int] = mapped_column(Integer, default=0)
    n_participants_total: Mapped[int] = mapped_column(Integer, default=0)
    experiment_versions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    software_versions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    results_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output_dir: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class GeneratedReport(Base):
    __tablename__ = "generated_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    kind: Mapped[str] = mapped_column(String(20))  # preliminary | final | presentation
    analysis_run_id: Mapped[int | None] = mapped_column(ForeignKey("analysis_runs.id"), nullable=True)
    output_dir: Mapped[str] = mapped_column(Text)
    files: Mapped[list] = mapped_column(JSON)


class AppSetting(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, onupdate=utcnow)
