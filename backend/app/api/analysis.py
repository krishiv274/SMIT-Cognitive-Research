"""Analysis endpoints: run, fetch results, download figures."""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..analysis.pipeline import run_and_store
from ..db import get_db
from ..models import AnalysisRun
from ..security import AdminDep

router = APIRouter(prefix="/api/admin/analysis", tags=["analysis"], dependencies=[AdminDep])


def _out(r: AnalysisRun, full: bool = True) -> dict:
    d = {"id": r.id, "created_at": r.created_at, "status": r.status, "dataset_hash": r.dataset_hash,
         "n_participants_included": r.n_participants_included, "n_participants_total": r.n_participants_total,
         "experiment_versions": r.experiment_versions, "error": r.error}
    if full:
        d["results"] = r.results_json
    return d


@router.post("/run")
def run(db: Session = Depends(get_db)) -> dict:
    try:
        r = run_and_store(db)
    except Exception as exc:
        raise HTTPException(500, f"Analysis failed: {exc}") from exc
    return _out(r)


@router.get("/runs")
def runs(db: Session = Depends(get_db)) -> list[dict]:
    return [_out(r, False) for r in db.scalars(select(AnalysisRun).order_by(AnalysisRun.id.desc()).limit(50)).all()]


@router.get("/latest")
def latest(db: Session = Depends(get_db)) -> dict | None:
    r = db.scalar(select(AnalysisRun).where(AnalysisRun.status == "completed").order_by(AnalysisRun.id.desc()))
    return _out(r) if r else None


@router.get("/{run_id}")
def get_run(run_id: int, db: Session = Depends(get_db)) -> dict:
    r = db.get(AnalysisRun, run_id)
    if r is None:
        raise HTTPException(404, "Analysis run not found")
    return _out(r)


def _fig_dir(db: Session, run_id: int) -> Path:
    r = db.get(AnalysisRun, run_id)
    if r is None or not r.output_dir:
        raise HTTPException(404, "Analysis run not found")
    return Path(r.output_dir) / "figures"


@router.get("/{run_id}/figures/{name}")
def figure(run_id: int, name: str, db: Session = Depends(get_db)):
    d = _fig_dir(db, run_id)
    p = (d / name).resolve()
    if d.resolve() not in p.parents or not p.is_file() or p.suffix not in (".png", ".svg", ".pdf"):
        raise HTTPException(404, "Figure not found")
    media = {".png": "image/png", ".svg": "image/svg+xml", ".pdf": "application/pdf"}[p.suffix]
    return FileResponse(p, media_type=media, filename=p.name)


@router.get("/{run_id}/figures.zip")
def figures_zip(run_id: int, db: Session = Depends(get_db)) -> Response:
    d = _fig_dir(db, run_id)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(d.glob("*")):
            z.write(f, f.name)
    return Response(buf.getvalue(), media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="SMIT_figures_run{run_id}.zip"'})
