"""Data import endpoints: upload -> validation preview -> confirm/cancel."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import ImportBatch
from ..security import AdminDep
from ..services import importer
from ..services.audit import audit
from ..settings import get_settings

router = APIRouter(prefix="/api/admin/import", tags=["import"], dependencies=[AdminDep])


def _out(b: ImportBatch) -> dict:
    return {"id": b.id, "file_names": b.file_names, "file_format": b.file_format, "import_kind": b.import_kind,
            "status": b.status, "created_at": b.created_at, "committed_at": b.committed_at,
            "n_participants": b.n_participants, "n_sessions": b.n_sessions, "n_trials": b.n_trials,
            "report": b.validation_report}


@router.post("/validate")
async def validate_upload(files: list[UploadFile] = File(...), db: Session = Depends(get_db)) -> dict:
    if not files or len(files) > 6:
        raise HTTPException(422, "Upload between 1 and 6 files.")
    limit = get_settings().max_upload_mb * 1024 * 1024
    payload = []
    for f in files:
        data = await f.read(limit + 1)
        if len(data) > limit:
            raise HTTPException(413, f"{f.filename} exceeds {get_settings().max_upload_mb} MB")
        name = (f.filename or "upload").replace("/", "_").replace("\\", "_")[-200:]
        payload.append((name, data))
    batch = importer.create_batch(db, payload)
    return _out(batch)


@router.post("/{batch_id}/commit")
def commit(batch_id: int, db: Session = Depends(get_db)) -> dict:
    b = db.get(ImportBatch, batch_id)
    if b is None:
        raise HTTPException(404, "Import not found")
    try:
        counts = importer.commit_batch(db, b)
    except importer.ImportRejected as exc:
        raise HTTPException(409, str(exc)) from exc
    # Trigger analysis on the newly validated dataset
    analysis_info = None
    try:
        from ..analysis.pipeline import run_and_store

        run = run_and_store(db)
        analysis_info = {"analysis_run_id": run.id, "n_participants_included": run.n_participants_included}
    except Exception as exc:  # analysis problems must not undo a valid import
        analysis_info = {"error": f"Import committed, but the automatic analysis failed: {exc}"}
    return {**_out(b), "committed": counts, "analysis": analysis_info}


@router.post("/{batch_id}/cancel")
def cancel(batch_id: int, db: Session = Depends(get_db)) -> dict:
    b = db.get(ImportBatch, batch_id)
    if b is None:
        raise HTTPException(404, "Import not found")
    if b.status == "committed":
        raise HTTPException(409, "A committed import cannot be cancelled; withdraw or delete participants instead.")
    b.status = "cancelled"
    b.staged_payload = None
    audit(db, "import_cancelled", entity_type="import", entity_id=str(batch_id))
    db.commit()
    return _out(b)


@router.get("")
def history(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(select(ImportBatch).order_by(ImportBatch.id.desc()).limit(100)).all()
    out = []
    for b in rows:
        d = _out(b)
        rep = d.pop("report") or {}
        d["n_errors"] = rep.get("n_errors")
        d["n_warnings"] = rep.get("n_warnings")
        out.append(d)
    return out


@router.get("/{batch_id}")
def get_batch(batch_id: int, db: Session = Depends(get_db)) -> dict:
    b = db.get(ImportBatch, batch_id)
    if b is None:
        raise HTTPException(404, "Import not found")
    return _out(b)
