"""Public endpoints used by the participant-facing experiment."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..experiment.config import ExperimentConfig
from ..models import ExperimentConfigVersion, ExperimentSession
from ..schemas import RegistrationIn, SessionEventIn, TrialBatchIn
from ..security import check_session_token, verify_token
from ..services import configs as config_service
from ..services import sessions as session_service
from ..settings import get_settings
from ..services import pilot_links, settings_store

router = APIRouter(prefix="/api/public", tags=["participant"])

STUDY_TITLE = ("Investigating the Effects of Numerical and Visual Interference on Spatial Working Memory "
               "and Cognitive Performance Among University Students")


@router.get("/study")
def study_info(pilot_token: str | None = None, db: Session = Depends(get_db)) -> dict:
    """Information shown on the welcome/consent screens. No hypotheses are revealed."""
    active = config_service.active_main_config(db)
    pilot_cfg = None
    if pilot_token:
        body = _pilot_token(pilot_token, db)
        pilot_cfg = db.get(ExperimentConfigVersion, body["config_id"])
        if pilot_cfg is None:
            # The configuration was deleted after the link was created: never fall back to the main study.
            raise HTTPException(403, "The configuration for this pilot link was deleted. Please ask the researcher "
                                     "for a new pilot link (Dashboard → Pilot mode → Start pilot session).")
    row = pilot_cfg or active
    cfg = ExperimentConfig.model_validate(row.config_json) if row else None
    return {
        "title": STUDY_TITLE,
        "short_title": "SMIT — Spatial Memory Interference Task",
        "purpose": ("This study looks at how people remember the positions of shapes for a few seconds "
                    "while doing other brief tasks."),
        "estimated_minutes": estimated_minutes(cfg),
        "main_study_open": active is not None,
        "mode": "pilot" if pilot_cfg else "main",
        "device_check_required": get_settings().require_device_check,
        "experiment_version": row.experiment_version if row else None,
        "config": cfg.to_json_dict() if cfg else None,
        "settings": settings_store.get_public(db),
    }


def estimated_minutes(cfg: ExperimentConfig | None) -> str:
    """Rough session length shown to participants, derived from the configuration (task + ~8 min of
    consent, instructions, practice feedback and breaks)."""
    if cfg is None:
        return "15–20"
    t, tr = cfg.timing, cfg.trials
    per_trial_ms = (t.fixation_ms + t.memory_stimulus_ms + t.post_stimulus_blank_ms + t.interference_ms
                    + t.retention_ms + 0.6 * t.recognition_deadline_ms + (t.iti_min_ms + t.iti_max_ms) / 2)
    n = 3 * (tr.trials_per_condition + tr.practice_per_condition)
    task_min = n * per_trial_ms / 60000 + 2 * t.break_min_s / 60
    lo = max(5, round((task_min + 6) / 5) * 5)
    return f"{lo}–{lo + 5}"


PILOT_LINK_INVALID = ("This pilot link has expired or is invalid. Please ask the researcher for a new "
                      "pilot link (Dashboard → Pilot mode → Start pilot session).")


def _pilot_token(token: str, db: Session) -> dict:
    """Validate a pilot link token (signature, expiry, revocation) with a participant-friendly message."""
    try:
        body = verify_token(token, "pilot")
    except HTTPException as exc:
        raise HTTPException(403, PILOT_LINK_INVALID) from exc
    if pilot_links.is_revoked(db, body):
        raise HTTPException(403, PILOT_LINK_INVALID)
    return body


def _get_session(db: Session, session_id: str, token: str | None) -> ExperimentSession:
    s = db.get(ExperimentSession, session_id)
    if s is None or not check_session_token(token, s.token_hash):
        raise HTTPException(404, "Session not found")
    return s


@router.post("/sessions")
def create_session(data: RegistrationIn, db: Session = Depends(get_db)) -> dict:
    if data.session_type == "pilot":
        if not data.pilot_token:
            raise HTTPException(403, "Pilot sessions must be launched from the researcher dashboard")
        body = _pilot_token(data.pilot_token, db)
        row = db.get(ExperimentConfigVersion, body["config_id"])
        if row is None:
            raise HTTPException(404, "Pilot configuration not found")
    else:
        row = config_service.active_main_config(db)
        if row is None:
            raise HTTPException(409, "The main study is not open yet: the researcher has not locked the "
                                     "experiment configuration.")
    return session_service.register(db, data, row)


@router.get("/sessions/{session_id}")
def resume_session(session_id: str, x_session_token: str | None = Header(default=None),
                   db: Session = Depends(get_db)) -> dict:
    """Return the plan and progress so an interrupted session can be resumed (no duplicate session)."""
    s = _get_session(db, session_id, x_session_token)
    cfg = db.get(ExperimentConfigVersion, s.config_id)
    return {"participant_id": s.participant_id, "session_id": s.session_id, "session_type": s.session_type,
            "condition_order": s.condition_order, "experiment_version": s.experiment_version,
            "config": cfg.config_json if cfg else None, "plan": s.trial_plan,
            "progress": session_service.progress(db, s)}


@router.post("/sessions/{session_id}/trials")
def submit_trials(session_id: str, batch: TrialBatchIn, x_session_token: str | None = Header(default=None),
                  db: Session = Depends(get_db)) -> dict:
    s = _get_session(db, session_id, x_session_token)
    return session_service.save_trials(db, s, batch.trials)


@router.post("/sessions/{session_id}/events")
def session_event(session_id: str, ev: SessionEventIn, x_session_token: str | None = Header(default=None),
                  db: Session = Depends(get_db)) -> dict:
    s = _get_session(db, session_id, x_session_token)
    return session_service.record_event(db, s, ev.event, ev.detail)


@router.get("/sessions/{session_id}/progress")
def session_progress(session_id: str, x_session_token: str | None = Header(default=None),
                     db: Session = Depends(get_db)) -> dict:
    s = _get_session(db, session_id, x_session_token)
    return session_service.progress(db, s)


@router.post("/sessions/{session_id}/complete")
def complete_session(session_id: str, x_session_token: str | None = Header(default=None),
                     db: Session = Depends(get_db)) -> dict:
    s = _get_session(db, session_id, x_session_token)
    return session_service.complete(db, s)
