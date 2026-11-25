"""Experiment configuration versioning, locking and audit."""
from __future__ import annotations

import json

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..experiment.config import ExperimentConfig, experiment_version_string
from ..models import ExperimentConfigVersion, ExperimentSession, utcnow
from ..settings import get_settings
from .audit import audit


def load_default_config() -> ExperimentConfig:
    path = get_settings().default_config_path
    return ExperimentConfig.model_validate(json.loads(path.read_text()))


def parse_config(data: dict) -> ExperimentConfig:
    try:
        return ExperimentConfig.model_validate(data)
    except Exception as exc:  # pydantic ValidationError
        raise HTTPException(422, f"Invalid configuration: {exc}") from exc


def _next_version_number(db: Session) -> int:
    return (db.scalar(select(func.max(ExperimentConfigVersion.version_number))) or 0) + 1


def create_config(db: Session, cfg: ExperimentConfig, *, notes: str | None = None,
                  parent_id: int | None = None, actor: str = "researcher") -> ExperimentConfigVersion:
    n = _next_version_number(db)
    h = cfg.canonical_hash()
    row = ExperimentConfigVersion(
        version_number=n, name=cfg.name, config_json=cfg.to_json_dict(), config_hash=h,
        experiment_version=experiment_version_string(n, h), status="draft", parent_id=parent_id, notes=notes,
    )
    db.add(row)
    db.flush()
    audit(db, "config_created", actor=actor, entity_type="config", entity_id=row.experiment_version,
          details={"parent_id": parent_id, "notes": notes, "deviations": cfg.deviates_from_specification()})
    return row


def ensure_default_config(db: Session) -> None:
    if db.scalar(select(func.count(ExperimentConfigVersion.id))) == 0:
        create_config(db, load_default_config(), notes="Initial default configuration from specification",
                      actor="system")
        db.commit()


def update_draft(db: Session, row: ExperimentConfigVersion, cfg: ExperimentConfig,
                 notes: str | None) -> ExperimentConfigVersion:
    if row.status != "draft":
        raise HTTPException(409, "Locked or retired configurations cannot be edited. Create a new draft version.")
    used = db.scalar(select(func.count()).select_from(ExperimentSession).where(ExperimentSession.config_id == row.id))
    if used:
        raise HTTPException(409, "This draft has already been used by pilot sessions; create a new draft "
                                 "version so earlier pilot data stay linked to the parameters they used.")
    old_hash = row.config_hash
    h = cfg.canonical_hash()
    row.config_json = cfg.to_json_dict()
    row.config_hash = h
    row.name = cfg.name
    row.experiment_version = experiment_version_string(row.version_number, h)
    if notes is not None:
        row.notes = notes
    audit(db, "config_draft_updated", entity_type="config", entity_id=row.experiment_version,
          details={"old_hash": old_hash[:8], "new_hash": h[:8]})
    return row


def lock_config(db: Session, row: ExperimentConfigVersion, justification: str) -> ExperimentConfigVersion:
    if row.status != "draft":
        raise HTTPException(409, "Only draft configurations can be locked")
    if not justification or len(justification.strip()) < 10:
        raise HTTPException(422, "Please give a justification (at least 10 characters) for locking")
    previous = db.scalars(select(ExperimentConfigVersion).where(ExperimentConfigVersion.is_active_main)).all()
    main_sessions_exist = db.scalar(
        select(func.count()).select_from(ExperimentSession).where(ExperimentSession.session_type == "main")
    )
    for p in previous:
        p.is_active_main = False
        p.status = "retired"
        audit(db, "config_retired", entity_type="config", entity_id=p.experiment_version,
              details={"replaced_by": row.experiment_version, "main_sessions_already_collected": main_sessions_exist})
    row.status = "locked"
    row.is_active_main = True
    row.locked_at = utcnow()
    row.lock_justification = justification.strip()
    cfg = ExperimentConfig.model_validate(row.config_json)
    audit(db, "config_locked", entity_type="config", entity_id=row.experiment_version,
          details={"justification": justification.strip(), "deviations_from_spec": cfg.deviates_from_specification(),
                   "replaced_active_configs": [p.experiment_version for p in previous],
                   "main_sessions_already_collected": main_sessions_exist})
    return row


def active_main_config(db: Session) -> ExperimentConfigVersion | None:
    return db.scalar(select(ExperimentConfigVersion).where(ExperimentConfigVersion.is_active_main))


def latest_draft(db: Session) -> ExperimentConfigVersion | None:
    return db.scalar(select(ExperimentConfigVersion).where(ExperimentConfigVersion.status == "draft")
                     .order_by(ExperimentConfigVersion.version_number.desc()))
