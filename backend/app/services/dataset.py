"""Build de-identified pandas DataFrames from the database (export + analysis)."""
from __future__ import annotations

import hashlib
import io
import json
import zipfile
from typing import Literal

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..data_dictionary import PARTICIPANT_VARS, SESSION_VARS, SUMMARY_VARS, TRIAL_VARS, names
from ..models import ExperimentSession, ImportedParticipantSummary, Participant, ParticipantContact, Trial

Scope = Literal["main", "pilot", "all"]

PARTICIPANT_EXPORT = names(PARTICIPANT_VARS) + ["participant_type", "status", "status_reason", "data_source", "created_at"]
SESSION_EXPORT = names(SESSION_VARS) + ["screen_information", "practice_attempts", "interruptions",
                                        "fullscreen_exits", "data_source"]
TRIAL_EXPORT = names(TRIAL_VARS)[:13] + ["premature_keypresses", "interference_type"] + names(TRIAL_VARS)[13:] + [
    "planned_iti_ms", "refresh_rate_hz", "dropped_frames", "timing_notes", "practice_attempt", "trial_id"]


def _scope_filter(stmt, model, scope: Scope):
    if scope == "all":
        return stmt
    return stmt.where(model.participant_type == scope)


def load_frames(db: Session, scope: Scope = "main") -> dict[str, pd.DataFrame]:
    pq = _scope_filter(select(Participant), Participant, scope).order_by(Participant.participant_id)
    participants = db.scalars(pq).all()
    pids = [p.participant_id for p in participants]
    prow = [{c: getattr(p, c) for c in PARTICIPANT_EXPORT} for p in participants]
    sq = select(ExperimentSession).where(ExperimentSession.participant_id.in_(pids)) if pids else None
    sessions = db.scalars(sq).all() if sq is not None else []
    srow = [{c: getattr(s, c) for c in SESSION_EXPORT} for s in sessions]
    sids = [s.session_id for s in sessions]
    trials = db.scalars(select(Trial).where(Trial.session_id.in_(sids))
                        .order_by(Trial.session_id, Trial.practice_trial.desc(), Trial.trial_number)).all() if sids else []
    trow = [{c: getattr(t, c) for c in TRIAL_EXPORT} for t in trials]
    summ = db.scalars(select(ImportedParticipantSummary).where(
        ImportedParticipantSummary.participant_id.in_(pids))).all() if pids else []
    sumrow = [{
        "participant_id": s.participant_id, "experiment_version": s.experiment_version,
        "condition_order": s.condition_order, "control_accuracy": s.accuracy_a, "numerical_accuracy": s.accuracy_b,
        "visual_accuracy": s.accuracy_c, "control_mean_correct_rt_ms": s.rt_a, "numerical_mean_correct_rt_ms": s.rt_b,
        "visual_mean_correct_rt_ms": s.rt_c, "timeout_rate": s.timeout_rate,
        "numerical_secondary_accuracy": s.secondary_accuracy_b, "visual_secondary_accuracy": s.secondary_accuracy_c,
    } for s in summ]
    return {
        "participants": pd.DataFrame(prow, columns=PARTICIPANT_EXPORT),
        "sessions": pd.DataFrame(srow, columns=SESSION_EXPORT),
        "trials": pd.DataFrame(trow, columns=TRIAL_EXPORT),
        "imported_summaries": pd.DataFrame(sumrow, columns=[v.name for v in SUMMARY_VARS if v.name not in
                                                            ("age", "gender", "academic_course", "consent_status")]),
    }


def dataset_hash(frames: dict[str, pd.DataFrame]) -> str:
    h = hashlib.sha256()
    for k in sorted(frames):
        df = frames[k]
        h.update(k.encode())
        h.update(df.to_csv(index=False).encode())
    return h.hexdigest()


def _safe(df: pd.DataFrame) -> pd.DataFrame:
    """Neutralise spreadsheet formula injection in exported text cells."""
    out = df.copy()
    for c in out.columns:
        if out[c].dtype == object:
            out[c] = out[c].map(lambda v: ("'" + v) if isinstance(v, str) and v[:1] in ("=", "+", "-", "@", "\t", "\r")
                                and not _is_number(v) else v)
    return out


def _is_number(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def _excel_ready(df: pd.DataFrame) -> pd.DataFrame:
    out = _safe(df)
    for c in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[c]) or out[c].map(lambda v: hasattr(v, "tzinfo")).any():
            out[c] = out[c].map(lambda v: v.isoformat() if hasattr(v, "isoformat") else v)
    return out


def export_bytes(db: Session, fmt: Literal["xlsx", "csv", "json"], scope: Scope = "main") -> tuple[bytes, str, str]:
    frames = load_frames(db, scope)
    frames = {"Participants": frames["participants"], "Sessions": frames["sessions"],
              "Raw_Trials": frames["trials"], "Imported_Summaries": frames["imported_summaries"]}
    stamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M")
    base = f"SMIT_deidentified_{scope}_{stamp}"
    if fmt == "json":
        payload = {k: json.loads(_excel_ready(v).to_json(orient="records", date_format="iso")) for k, v in frames.items()}
        payload["_meta"] = {"scope": scope, "exported_at": pd.Timestamp.now().isoformat(),
                            "note": "De-identified export: contains no email addresses."}
        return json.dumps(payload, indent=2, default=str).encode(), f"{base}.json", "application/json"
    if fmt == "csv":
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for k, v in frames.items():
                z.writestr(f"{k}.csv", _excel_ready(v).to_csv(index=False))
        return buf.getvalue(), f"{base}_csv.zip", "application/zip"
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for k, v in frames.items():
            _excel_ready(v).to_excel(xw, sheet_name=k, index=False)
            ws = xw.sheets[k]
            ws.freeze_panes = "A2"
            if ws.max_row > 1:
                ws.auto_filter.ref = ws.dimensions
    return buf.getvalue(), f"{base}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def contacts_csv(db: Session) -> bytes:
    rows = db.execute(select(ParticipantContact.participant_id, ParticipantContact.email)
                      .order_by(ParticipantContact.participant_id)).all()
    df = pd.DataFrame(rows, columns=["participant_id", "email"])
    return _safe(df).to_csv(index=False).encode()
