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
from ..services import settings_store

router = APIRouter(prefix="/api/public", tags=["participant"])

STUDY_TITLE = ("Investigating the Effects of Numerical and Visual Interference on Spatial Working Memory "
               "and Cognitive Performance Among University Students")


@router.get("/study")
def study_info(pilot_token: str | None = None, db: Session = Depends(get_db)) -> dict:
    """Information shown on the welcome/consent screens. No hypotheses are revealed."""
    active = config_service.active_main_config(db)
    pilot_cfg = None
    if pilot_token:
        body = _pilot_token(pilot_token)
        pilot_cfg = db.get(ExperimentConfigVersion, body["config_id"])
    row = pilot_cfg or active
    cfg = ExperimentConfig.model_validate(row.config_json) if row else None
    return {
        "title": STUDY_TITLE,
        "short_title": "SMIT — Spatial Memory Interference Task",
        "purpose": ("This study looks at how people remember the positions of shapes for a few seconds "
                    "while doing other brief tasks."),
        "estimated_minutes": "15–20",
        "main_study_open": active is not None,
        "mode": "pilot" if pilot_cfg else "main",
        "experiment_version": row.experiment_version if row else None,
        "config": cfg.to_json_dict() if cfg else None,
        "settings": settings_store.get_public(db),
    }


def _pilot_token(token: str) -> dict:
    """Validate a pilot link token with a participant-friendly error message."""
    try:
        return verify_token(token, "pilot")
    except HTTPException as exc:
        raise HTTPException(403, "This pilot link has expired or is invalid. Please ask the researcher for a new "
                                 "pilot link (Dashboard → Pilot mode → Start pilot session).") from exc


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
        body = _pilot_token(data.pilot_token)
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
