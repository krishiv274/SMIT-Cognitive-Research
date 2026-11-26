"""Researcher dashboard API (requires researcher login)."""
from __future__ import annotations

import time
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..experiment.config import ExperimentConfig
from ..experiment.plan import generate_plan
from ..models import (
    AuditLog,
    ExperimentConfigVersion,
    ExperimentSession,
    Participant,
    ParticipantContact,
    Trial,
)
from ..schemas import (
    ConfigIn,
    DeleteIn,
    LockIn,
    LoginIn,
    PilotLaunchIn,
    SessionStatusIn,
    StatusChangeIn,
    TrialExclusionIn,
)
from ..security import AdminDep, check_admin_password, issue_admin_token, sign_token
from ..services import configs as config_service
from ..services import dataset as dataset_service
from ..services import settings_store
from ..services.audit import audit
from ..services.sessions import order_counts
from ..settings import get_settings

router = APIRouter(prefix="/api/admin", tags=["researcher"])
TARGET_N = 20


_FAILED_LOGINS: list[float] = []
MAX_FAILED_LOGINS = 10          # within LOCKOUT_WINDOW_S
LOCKOUT_WINDOW_S = 15 * 60


@router.post("/login")
def login(data: LoginIn) -> dict:
    now = time.time()
    _FAILED_LOGINS[:] = [t for t in _FAILED_LOGINS if now - t < LOCKOUT_WINDOW_S]
    if len(_FAILED_LOGINS) >= MAX_FAILED_LOGINS:
        raise HTTPException(429, "Too many failed login attempts. Researcher login is locked for 15 minutes.")
    if not check_admin_password(data.password):
        _FAILED_LOGINS.append(now)
        time.sleep(0.8)  # slow down brute force
        raise HTTPException(401, "Incorrect password")
    return {"token": issue_admin_token(), "default_password_in_use": get_settings().using_default_password}


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------

@router.get("/overview", dependencies=[AdminDep])
def overview(db: Session = Depends(get_db)) -> dict:
    parts = db.scalars(select(Participant)).all()
    sessions = db.scalars(select(ExperimentSession)).all()
    main_parts = [p for p in parts if p.participant_type == "main"]
    main_sessions = [s for s in sessions if s.session_type == "main"]
    completed_ids = {s.participant_id for s in main_sessions if s.completion_status == "completed"}
    eligible_completed = [p for p in main_parts if p.participant_id in completed_ids and p.status == "active"]
    imported_summary_ids = [p.participant_id for p in main_parts if p.imported_summary is not None]
    valid_trials = db.scalar(
        select(func.count()).select_from(Trial).join(ExperimentSession)
        .where(ExperimentSession.session_type == "main", Trial.practice_trial.is_(False),
               Trial.timing_quality_flag != "invalid", Trial.exclusion_status == "included")) or 0
    total_trials = db.scalar(
        select(func.count()).select_from(Trial).join(ExperimentSession)
        .where(ExperimentSession.session_type == "main", Trial.practice_trial.is_(False))) or 0
    active = config_service.active_main_config(db)
    n_complete = len(eligible_completed) + len([i for i in imported_summary_ids if
                                                 next(p for p in main_parts if p.participant_id == i).status == "active"])
    return {
        "target_participants": TARGET_N,
        "registered_participants": len(main_parts),
        "completed_participants": n_complete,
        "incomplete_sessions": sum(1 for s in main_sessions if s.completion_status in ("registered", "in_progress",
                                                                                     "incomplete", "abandoned")),
        "withdrawn_participants": sum(1 for p in main_parts if p.status == "withdrawn"),
        "excluded_participants": sum(1 for p in main_parts if p.status == "excluded"),
        "valid_experimental_trials": valid_trials,
        "total_experimental_trials": total_trials,
        "pilot_sessions": sum(1 for s in sessions if s.session_type == "pilot"),
        "imported_summary_only_participants": len(imported_summary_ids),
        "condition_order_distribution": order_counts(db, "main"),
        "gender_distribution": dict(Counter(p.gender or "Missing" for p in main_parts if p.status == "active")),
        "course_distribution": dict(Counter(p.academic_course or "Missing" for p in main_parts if p.status == "active")),
        "age_values": sorted(p.age for p in main_parts if p.age is not None and p.status == "active"),
        "progress_percent": min(100.0, round(100 * n_complete / TARGET_N, 1)),
        "active_config": ({"id": active.id, "experiment_version": active.experiment_version,
                           "locked_at": active.locked_at} if active else None),
        "default_password_in_use": get_settings().using_default_password,
    }


# ---------------------------------------------------------------------------
# Participants
# ---------------------------------------------------------------------------

def _participant_or_404(db: Session, pid: str) -> Participant:
    p = db.scalar(select(Participant).where(Participant.participant_id == pid))
    if p is None:
        raise HTTPException(404, "Participant not found")
    return p


@router.get("/participants", dependencies=[AdminDep])
def list_participants(scope: str = Query("all", pattern="^(main|pilot|all)$"), db: Session = Depends(get_db)) -> list[dict]:
    q = select(Participant).order_by(Participant.created_at.desc())
    if scope != "all":
        q = q.where(Participant.participant_type == scope)
    out = []
    for p in db.scalars(q).all():
        sess = sorted(p.sessions, key=lambda s: s.created_at)
        counts = {}
        for s in sess:
            counts[s.session_id] = db.scalar(select(func.count()).select_from(Trial).where(
                Trial.session_id == s.session_id, Trial.practice_trial.is_(False))) or 0
        out.append({
            "participant_id": p.participant_id, "participant_type": p.participant_type, "age": p.age,
            "gender": p.gender, "academic_course": p.academic_course, "consent_status": p.consent_status,
            "consent_timestamp": p.consent_timestamp, "status": p.status, "status_reason": p.status_reason,
            "data_source": p.data_source, "created_at": p.created_at,
            "has_contact": bool(p.contact and p.contact.email),
            "summary_only": p.imported_summary is not None,
            "sessions": [{"session_id": s.session_id, "completion_status": s.completion_status,
                          "condition_order": s.condition_order, "experiment_version": s.experiment_version,
                          "main_trials_saved": counts[s.session_id],
                          "n_main_planned": (s.trial_plan or {}).get("n_main"),
                          "created_at": s.created_at, "interruptions": s.interruptions} for s in sess],
        })
    return out


@router.post("/participants/{pid}/status", dependencies=[AdminDep])
def set_participant_status(pid: str, data: StatusChangeIn, db: Session = Depends(get_db)) -> dict:
    p = _participant_or_404(db, pid)
    old = p.status
    p.status = data.status
    p.status_reason = data.reason
    audit(db, "participant_status_changed", entity_type="participant", entity_id=pid,
          details={"from": old, "to": data.status, "reason": data.reason})
    db.commit()
    return {"participant_id": pid, "status": p.status}


@router.delete("/participants/{pid}", dependencies=[AdminDep])
def delete_participant(pid: str, data: DeleteIn, db: Session = Depends(get_db)) -> dict:
    if data.confirm_participant_id != pid:
        raise HTTPException(422, "Type the participant ID exactly to confirm deletion")
    p = _participant_or_404(db, pid)
    n_sessions = len(p.sessions)
    n_trials = sum(len(s.trials) for s in p.sessions)
    db.delete(p)
    audit(db, "participant_deleted", entity_type="participant", entity_id=pid,
          details={"reason": data.reason, "sessions_deleted": n_sessions, "trials_deleted": n_trials})
    db.commit()
    return {"deleted": pid, "sessions": n_sessions, "trials": n_trials}


@router.get("/participants/{pid}/contact", dependencies=[AdminDep])
def get_contact(pid: str, db: Session = Depends(get_db)) -> dict:
    c = db.scalar(select(ParticipantContact).where(ParticipantContact.participant_id == pid))
    audit(db, "contact_viewed", entity_type="participant", entity_id=pid)
    db.commit()
    return {"participant_id": pid, "email": c.email if c else None}


@router.get("/contacts/export", dependencies=[AdminDep])
def export_contacts(db: Session = Depends(get_db)) -> Response:
    data = dataset_service.contacts_csv(db)
    audit(db, "contacts_exported", entity_type="contacts")
    db.commit()
    return Response(data, media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="SMIT_CONFIDENTIAL_contacts.csv"'})


# ---------------------------------------------------------------------------
# Sessions and trials
# ---------------------------------------------------------------------------

@router.get("/sessions/{session_id}", dependencies=[AdminDep])
def session_detail(session_id: str, db: Session = Depends(get_db)) -> dict:
    s = db.get(ExperimentSession, session_id)
    if s is None:
        raise HTTPException(404, "Session not found")
    trials = db.scalars(select(Trial).where(Trial.session_id == session_id)
                        .order_by(Trial.practice_trial.desc(), Trial.practice_attempt, Trial.trial_number)).all()
    cols = [c.name for c in Trial.__table__.columns]
    tl = [{c: getattr(t, c) for c in cols} for t in trials]
    timing = {}
    for name, pk, mk in (("fixation", "planned_fixation_duration_ms", "actual_fixation_duration_ms"),
                         ("memory_stimulus", "planned_stimulus_duration_ms", "measured_stimulus_duration_ms"),
                         ("interference", "planned_interference_duration_ms", "measured_interference_duration_ms"),
                         ("retention", "planned_retention_duration_ms", "measured_retention_duration_ms")):
        devs = [getattr(t, mk) - getattr(t, pk) for t in trials if getattr(t, mk) is not None and getattr(t, pk) is not None]
        if devs:
            devs_sorted = sorted(devs)
            timing[name] = {"n": len(devs), "mean_deviation_ms": sum(devs) / len(devs),
                            "max_abs_deviation_ms": max(abs(d) for d in devs),
                            "median_deviation_ms": devs_sorted[len(devs) // 2]}
    return {
        "session": {c.name: getattr(s, c.name) for c in ExperimentSession.__table__.columns
                    if c.name not in ("token_hash", "trial_plan")},
        "plan": s.trial_plan,
        "trials": tl,
        "timing_summary": timing,
        "flags": dict(Counter(t.timing_quality_flag for t in trials)),
    }


@router.post("/sessions/{session_id}/status", dependencies=[AdminDep])
def set_session_status(session_id: str, data: SessionStatusIn, db: Session = Depends(get_db)) -> dict:
    s = db.get(ExperimentSession, session_id)
    if s is None:
        raise HTTPException(404, "Session not found")
    old = s.completion_status
    s.completion_status = data.completion_status
    audit(db, "session_status_changed", entity_type="session", entity_id=session_id,
          details={"from": old, "to": data.completion_status, "reason": data.reason})
    db.commit()
    return {"session_id": session_id, "completion_status": s.completion_status}


@router.post("/trials/{trial_id}/exclusion", dependencies=[AdminDep])
def set_trial_exclusion(trial_id: int, data: TrialExclusionIn, db: Session = Depends(get_db)) -> dict:
    t = db.get(Trial, trial_id)
    if t is None:
        raise HTTPException(404, "Trial not found")
    t.exclusion_status = "excluded" if data.excluded else "included"
    t.exclusion_reason = data.reason
    audit(db, "trial_exclusion_changed", entity_type="trial", entity_id=str(trial_id),
          details={"excluded": data.excluded, "reason": data.reason, "session_id": t.session_id})
    db.commit()
    return {"trial_id": trial_id, "exclusion_status": t.exclusion_status}


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def _cfg_out(row: ExperimentConfigVersion, db: Session) -> dict:
    cfg = ExperimentConfig.model_validate(row.config_json)
    used = db.scalar(select(func.count()).select_from(ExperimentSession).where(ExperimentSession.config_id == row.id))
    return {"id": row.id, "version_number": row.version_number, "name": row.name,
            "experiment_version": row.experiment_version, "status": row.status, "is_active_main": row.is_active_main,
            "config": row.config_json, "config_hash": row.config_hash, "parent_id": row.parent_id, "notes": row.notes,
            "lock_justification": row.lock_justification, "created_at": row.created_at, "locked_at": row.locked_at,
            "sessions_using": used, "deviations_from_specification": cfg.deviates_from_specification()}


@router.get("/configs", dependencies=[AdminDep])
def list_configs(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(select(ExperimentConfigVersion).order_by(ExperimentConfigVersion.version_number.desc())).all()
    return [_cfg_out(r, db) for r in rows]


@router.get("/configs/default", dependencies=[AdminDep])
def default_config() -> dict:
    return config_service.load_default_config().to_json_dict()


@router.post("/configs", dependencies=[AdminDep])
def create_config(data: ConfigIn, db: Session = Depends(get_db)) -> dict:
    cfg = config_service.parse_config(data.config)
    row = config_service.create_config(db, cfg, notes=data.notes, parent_id=data.parent_id)
    db.commit()
    return _cfg_out(row, db)


@router.put("/configs/{config_id}", dependencies=[AdminDep])
def update_config(config_id: int, data: ConfigIn, db: Session = Depends(get_db)) -> dict:
    row = db.get(ExperimentConfigVersion, config_id)
    if row is None:
        raise HTTPException(404, "Configuration not found")
    cfg = config_service.parse_config(data.config)
    config_service.update_draft(db, row, cfg, data.notes)
    db.commit()
    return _cfg_out(row, db)


@router.post("/configs/{config_id}/lock", dependencies=[AdminDep])
def lock_config(config_id: int, data: LockIn, db: Session = Depends(get_db)) -> dict:
    row = db.get(ExperimentConfigVersion, config_id)
    if row is None:
        raise HTTPException(404, "Configuration not found")
    config_service.lock_config(db, row, data.justification)
    db.commit()
    return _cfg_out(row, db)


@router.get("/configs/{config_id}/preview", dependencies=[AdminDep])
def preview_plan(config_id: int, seed: int = 1, order: str = "ABC", db: Session = Depends(get_db)) -> dict:
    row = db.get(ExperimentConfigVersion, config_id)
    if row is None:
        raise HTTPException(404, "Configuration not found")
    cfg = ExperimentConfig.model_validate(row.config_json)
    try:
        return {"config": row.config_json, "plan": generate_plan(cfg, seed, order)}
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


# ---------------------------------------------------------------------------
# Pilot mode
# ---------------------------------------------------------------------------

@router.post("/pilot/launch", dependencies=[AdminDep])
def launch_pilot(data: PilotLaunchIn, db: Session = Depends(get_db)) -> dict:
    row = db.get(ExperimentConfigVersion, data.config_id) if data.config_id else (
        config_service.latest_draft(db) or config_service.active_main_config(db))
    if row is None:
        raise HTTPException(404, "No configuration available")
    token = sign_token({"kind": "pilot", "config_id": row.id}, 6 * 3600)
    audit(db, "pilot_launched", entity_type="config", entity_id=row.experiment_version)
    db.commit()
    return {"pilot_token": token, "url": f"/participate?pilot={token}", "experiment_version": row.experiment_version}


# ---------------------------------------------------------------------------
# Export / settings / audit
# ---------------------------------------------------------------------------

@router.get("/export", dependencies=[AdminDep])
def export_data(fmt: str = Query("xlsx", pattern="^(xlsx|csv|json)$"),
                scope: str = Query("main", pattern="^(main|pilot|all)$"), db: Session = Depends(get_db)) -> Response:
    data, filename, mime = dataset_service.export_bytes(db, fmt, scope)  # type: ignore[arg-type]
    audit(db, "data_exported", entity_type="dataset", details={"format": fmt, "scope": scope, "deidentified": True})
    db.commit()
    return Response(data, media_type=mime, headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/settings", dependencies=[AdminDep])
def get_settings_values(db: Session = Depends(get_db)) -> dict:
    return settings_store.get_all(db)


@router.put("/settings", dependencies=[AdminDep])
def put_settings(values: dict[str, str], db: Session = Depends(get_db)) -> dict:
    out = settings_store.update(db, values)
    db.commit()
    return out


@router.get("/audit", dependencies=[AdminDep])
def audit_log(limit: int = Query(200, le=2000), db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)).all()
    return [{"id": r.id, "timestamp": r.timestamp, "actor": r.actor, "action": r.action,
             "entity_type": r.entity_type, "entity_id": r.entity_id, "details": r.details} for r in rows]
