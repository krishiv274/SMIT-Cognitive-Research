"""Participant registration, session creation, trial storage and completion."""
from __future__ import annotations

import json
import secrets

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..experiment.config import ExperimentConfig
from ..experiment.plan import ORDERS, assign_condition_order, generate_plan, pattern_to_str
from ..models import (
    ExperimentConfigVersion,
    ExperimentSession,
    Participant,
    ParticipantContact,
    Trial,
    utcnow,
)
from ..schemas import RegistrationIn, TrialIn
from ..security import email_hash, new_session_token
from .audit import audit
from .timing import assess_timing


def next_participant_id(db: Session, session_type: str) -> str:
    prefix = "P" if session_type == "main" else "PILOT-"
    existing = db.scalars(select(Participant.participant_id).where(Participant.participant_id.like(f"{prefix}%"))).all()
    nums = []
    for pid in existing:
        tail = pid[len(prefix):]
        if tail.isdigit():
            nums.append(int(tail))
    n = (max(nums) if nums else 0) + 1
    return f"{prefix}{n:03d}"


def order_counts(db: Session, session_type: str) -> dict[str, int]:
    rows = db.execute(
        select(ExperimentSession.condition_order, func.count())
        .join(Participant, Participant.participant_id == ExperimentSession.participant_id)
        .where(ExperimentSession.session_type == session_type)
        .where(ExperimentSession.completion_status.notin_(["withdrawn", "abandoned"]))
        .where(Participant.status != "withdrawn")
        .group_by(ExperimentSession.condition_order)
    ).all()
    return {o: 0 for o in ORDERS} | {r[0]: r[1] for r in rows}


def register(db: Session, data: RegistrationIn, config_row: ExperimentConfigVersion) -> dict:
    if not data.consent:
        raise HTTPException(400, "Consent is required to take part")
    is_main = data.session_type == "main"
    if is_main:
        missing = [f for f in ("age", "gender", "academic_course", "email") if getattr(data, f) in (None, "")]
        if missing:
            raise HTTPException(422, f"Missing required fields: {', '.join(missing)}")
    if data.age is not None and not (18 <= data.age <= 120):
        raise HTTPException(422, "Participants must be 18 years or older (age 18–120)")

    ehash = email_hash(data.email) if data.email else None
    if is_main and ehash:
        dup = db.scalar(
            select(ParticipantContact.participant_id)
            .join(Participant, Participant.participant_id == ParticipantContact.participant_id)
            .where(ParticipantContact.email_hash == ehash, Participant.participant_type == "main")
        )
        if dup:
            raise HTTPException(409, "This email address is already registered for the main study. "
                                     "Each person may take part only once. Please speak to the researcher.")

    cfg = ExperimentConfig.model_validate(config_row.config_json)
    for _ in range(5):
        pid = next_participant_id(db, data.session_type)
        order = assign_condition_order(order_counts(db, data.session_type))
        seed = secrets.randbelow(2**31 - 1)
        plan = generate_plan(cfg, seed, order)
        token, token_hash = new_session_token()
        participant = Participant(
            participant_id=pid, age=data.age, gender=data.gender, academic_course=data.academic_course,
            consent_status=True, consent_timestamp=utcnow(), participant_type=data.session_type,
        )
        participant.contact = ParticipantContact(email=data.email, email_hash=ehash)
        session = ExperimentSession(
            session_id=secrets.token_hex(16), participant_id=pid, config_id=config_row.id,
            experiment_version=config_row.experiment_version, session_type=data.session_type,
            condition_order=order, random_seed=seed, trial_plan=plan,
            device_information=json.dumps({k: v for k, v in data.device.model_dump().items()
                                           if k not in ("user_agent",)}),
            browser_information=(data.device.user_agent or "")[:500],
            screen_information=(f"{data.device.screen_width}x{data.device.screen_height}@{data.device.device_pixel_ratio or 1}"
                                if data.device.screen_width and data.device.screen_height else None),
            estimated_refresh_rate=data.device.estimated_refresh_rate,
            completion_status="registered", token_hash=token_hash,
        )
        participant.sessions.append(session)
        db.add(participant)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            continue
        audit(db, "session_created", actor="participant", entity_type="session", entity_id=session.session_id,
              details={"participant_id": pid, "session_type": data.session_type, "condition_order": order,
                       "experiment_version": config_row.experiment_version})
        db.commit()
        return {
            "participant_id": pid, "session_id": session.session_id, "session_token": token,
            "session_type": data.session_type, "condition_order": order,
            "experiment_version": config_row.experiment_version, "config": cfg.to_json_dict(), "plan": plan,
        }
    raise HTTPException(500, "Could not allocate a participant ID, please retry")


def plan_trial(session: ExperimentSession, practice: bool, number: int) -> dict:
    plan = session.trial_plan or {}
    if practice:
        for t in plan.get("practice", []):
            if t["trial_number"] == number:
                return t
    else:
        for b in plan.get("blocks", []):
            for t in b["trials"]:
                if t["trial_number"] == number:
                    return t
    raise HTTPException(422, f"Trial {number} (practice={practice}) is not part of this session's plan")


def save_trials(db: Session, session: ExperimentSession, trials: list[TrialIn]) -> dict:
    if session.completion_status in ("withdrawn", "abandoned"):
        raise HTTPException(409, f"Session is {session.completion_status}; no more data accepted")
    cfg = ExperimentConfig.model_validate(db.get(ExperimentConfigVersion, session.config_id).config_json)
    deadline = cfg.timing.recognition_deadline_ms
    saved, duplicates = [], []
    seen: set[tuple] = set()
    for t in trials:
        key = (session.session_id, t.practice_trial, t.practice_attempt if t.practice_trial else 0, t.trial_number)
        if key in seen:  # the same trial twice in one upload: keep the first copy
            duplicates.append(t.trial_number)
            continue
        seen.add(key)
        exists = db.scalar(select(Trial.trial_id).where(
            Trial.session_id == key[0], Trial.practice_trial == key[1],
            Trial.practice_attempt == key[2], Trial.trial_number == key[3]))
        if exists:
            duplicates.append(t.trial_number)
            continue
        p = plan_trial(session, t.practice_trial, t.trial_number)
        notes = []
        response = t.participant_response
        rt = t.reaction_time_ms
        timeout = bool(t.response_timeout or response is None)
        if timeout:
            response, rt = None, None
        if rt is not None and (rt < 0 or rt > deadline + 50):
            notes.append(f"reported RT {rt:.1f} ms outside response window; discarded")
            rt, response, timeout = None, None, True
        is_correct = None if timeout else (response == p["correct_answer"])
        sec = p.get("interference")
        i_resp = t.interference_response if sec else None
        i_rt = t.interference_reaction_time_ms if (sec and i_resp is not None) else None
        i_acc = None
        if sec:
            i_acc = (i_resp == sec["correct"]) if i_resp is not None else False
        row = dict(
            session_id=session.session_id, participant_id=session.participant_id,
            trial_number=t.trial_number, block_number=p["block_number"], condition=p["condition"],
            practice_trial=t.practice_trial, practice_attempt=key[2],
            original_pattern=pattern_to_str(p["original_pattern"]),
            recognition_pattern=pattern_to_str(p["recognition_pattern"]),
            correct_answer=p["correct_answer"], participant_response=response, is_correct=is_correct,
            reaction_time_ms=rt, response_timeout=timeout, premature_keypresses=t.premature_keypresses,
            interference_type=p["interference_type"],
            interference_stimulus=(sec["text"] if sec else None),
            interference_correct_answer=(sec["correct"] if sec else None),
            interference_response=i_resp, interference_accuracy=i_acc, interference_reaction_time_ms=i_rt,
            planned_fixation_duration_ms=p["planned_fixation_ms"],
            actual_fixation_duration_ms=t.actual_fixation_duration_ms,
            planned_stimulus_duration_ms=p["planned_memory_stimulus_ms"],
            measured_stimulus_duration_ms=t.measured_stimulus_duration_ms,
            planned_interference_duration_ms=p["planned_interference_ms"],
            measured_interference_duration_ms=t.measured_interference_duration_ms,
            planned_retention_duration_ms=p["planned_retention_ms"],
            measured_retention_duration_ms=t.measured_retention_duration_ms,
            planned_iti_ms=p["planned_iti_ms"], inter_trial_interval_ms=t.inter_trial_interval_ms,
            refresh_rate_hz=t.refresh_rate_hz or session.estimated_refresh_rate,
            dropped_frames=t.dropped_frames, focus_loss=t.focus_loss,
            event_timestamps=t.event_timestamps if session.session_type == "pilot" or t.event_timestamps else None,
        )
        flag, tnotes = assess_timing(row, row["refresh_rate_hz"], cfg.analysis)
        if tnotes:
            notes.append(tnotes)
        row["timing_quality_flag"] = flag
        row["timing_notes"] = "; ".join(notes) or None
        db.add(Trial(**row))
        saved.append(t.trial_number)
    if session.completion_status == "registered":
        session.completion_status = "in_progress"
        session.start_time = session.start_time or utcnow()
    session.last_activity = utcnow()
    try:
        db.commit()
    except IntegrityError:  # concurrent duplicate submission
        db.rollback()
        raise HTTPException(409, "Duplicate trial submission detected; please retry")
    return {"saved": saved, "duplicates": duplicates}


def progress(db: Session, session: ExperimentSession) -> dict:
    rows = db.execute(select(Trial.trial_number, Trial.practice_trial).where(
        Trial.session_id == session.session_id)).all()
    main = sorted({r[0] for r in rows if not r[1]})
    plan = session.trial_plan or {}
    return {
        "session_id": session.session_id, "participant_id": session.participant_id,
        "completion_status": session.completion_status, "saved_main_trials": main,
        "n_main_planned": plan.get("n_main", 0), "practice_trials_saved": sum(1 for r in rows if r[1]),
    }


def complete(db: Session, session: ExperimentSession) -> dict:
    prog = progress(db, session)
    n_saved, n_planned = len(prog["saved_main_trials"]), prog["n_main_planned"]
    if session.completion_status not in ("withdrawn", "abandoned"):
        was_completed = session.completion_status == "completed"
        session.completion_status = "completed" if n_saved >= n_planned else "incomplete"
        # Calling /complete again (e.g. after a resume or retry) must not move the original completion time.
        if not (was_completed and session.completion_time):
            session.completion_time = utcnow()
    audit(db, "session_completed" if session.completion_status == "completed" else "session_incomplete",
          actor="participant", entity_type="session", entity_id=session.session_id,
          details={"main_trials_saved": n_saved, "planned": n_planned})
    db.commit()
    return {**prog, "completion_status": session.completion_status, "main_trials_saved": n_saved}


def record_event(db: Session, session: ExperimentSession, event: str, detail: str | None) -> dict:
    if event == "practice_started" or event == "practice_repeated":
        session.practice_attempts += 1
    elif event == "main_started":
        session.start_time = session.start_time or utcnow()
        if session.completion_status == "registered":
            session.completion_status = "in_progress"
    elif event == "interrupted":
        session.interruptions += 1
    elif event == "fullscreen_exit":
        session.fullscreen_exits += 1
    elif event == "withdrawn":
        session.completion_status = "withdrawn"
        session.completion_time = utcnow()
        p = db.scalar(select(Participant).where(Participant.participant_id == session.participant_id))
        if p:
            p.status = "withdrawn"
            p.status_reason = "Participant stopped the task and chose to withdraw"
    session.last_activity = utcnow()
    audit(db, f"session_event:{event}", actor="participant", entity_type="session", entity_id=session.session_id,
          details={"detail": (detail or "")[:200]})
    db.commit()
    return {"ok": True, "completion_status": session.completion_status}
