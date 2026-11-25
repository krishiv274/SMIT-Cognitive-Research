"""Report, presentation and template endpoints."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import GeneratedReport
from ..reports.generate import generate_presentation, generate_report
from ..security import AdminDep
from ..settings import REPO_ROOT

router = APIRouter(prefix="/api/admin", tags=["reports"], dependencies=[AdminDep])
TEMPLATE_DIR = REPO_ROOT / "templates"
MIME = {".pdf": "application/pdf", ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".html": "text/html", ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation", ".csv": "text/csv"}


def _out(r: GeneratedReport) -> dict:
    return {"id": r.id, "created_at": r.created_at, "kind": r.kind, "analysis_run_id": r.analysis_run_id, "files": r.files}


@router.post("/reports/generate")
def gen_report(db: Session = Depends(get_db)) -> dict:
    try:
        r = generate_report(db)
    except Exception as exc:
        raise HTTPException(500, f"Report generation failed: {exc}") from exc
    msg = ("Final report generated from the latest analysis run. Review every automatically drafted interpretation before submission."
           if r.kind == "final" else
           "Preliminary report generated: no analysis run with eligible genuine data was available, so Results, Discussion and "
           "Conclusion are marked as pending. Run the analysis after data collection and generate again.")
    return {**_out(r), "message": msg}


@router.post("/reports/presentation")
def gen_presentation(db: Session = Depends(get_db)) -> dict:
    try:
        r = generate_presentation(db)
    except Exception as exc:
        raise HTTPException(500, f"Presentation generation failed: {exc}") from exc
    return {**_out(r), "message": "Presentation generated" + (" with results from the latest analysis." if r.analysis_run_id else " (results pending).")}


@router.get("/reports")
def list_reports(db: Session = Depends(get_db)) -> list[dict]:
    return [_out(r) for r in db.scalars(select(GeneratedReport).order_by(GeneratedReport.id.desc()).limit(50)).all()]


@router.get("/reports/{report_id}/files/{name}")
def report_file(report_id: int, name: str, db: Session = Depends(get_db)):
    r = db.get(GeneratedReport, report_id)
    if r is None or name not in {f["name"] for f in r.files}:
        raise HTTPException(404, "File not found")
    p = Path(r.output_dir) / name
    if not p.is_file():
        raise HTTPException(404, "File missing on disk")
    return FileResponse(p, media_type=MIME.get(p.suffix, "application/octet-stream"), filename=name)


@router.get("/templates/{name}")
def template(name: str):
    p = (TEMPLATE_DIR / name).resolve()
    if TEMPLATE_DIR.resolve() not in p.parents or not p.is_file():
        raise HTTPException(404, "Template not found")
    return FileResponse(p, media_type=MIME.get(p.suffix, "application/octet-stream"), filename=p.name)
