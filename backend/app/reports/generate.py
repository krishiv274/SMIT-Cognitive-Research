"""Generate report files (PDF/DOCX/HTML/XLSX) and the presentation."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..experiment.config import ExperimentConfig
from ..models import AnalysisRun, ExperimentConfigVersion, GeneratedReport
from ..services import settings_store
from ..services.audit import audit
from ..services.configs import active_main_config, load_default_config
from ..settings import get_settings
from .builder import build
from .excel_results import write_results_workbook
from .presentation import build_presentation
from .render import to_docx, to_html, to_pdf


def _config_and_version(db: Session | None, results: dict | None) -> tuple[ExperimentConfig, str | None]:
    if db is not None:
        versions = (results or {}).get("meta", {}).get("experiment_versions") or []
        row = None
        if versions:
            row = db.scalar(select(ExperimentConfigVersion).where(ExperimentConfigVersion.experiment_version == versions[0]))
        row = row or active_main_config(db)
        if row:
            return ExperimentConfig.model_validate(row.config_json), row.experiment_version
    return load_default_config(), None


def write_report_files(out_dir: Path, cfg: ExperimentConfig, settings: dict, results: dict | None,
                       figdir: Path | None, version: str | None, basename: str | None = None) -> tuple[list[dict], bool]:
    from ..reports import design_figures

    # Draw the design figures for THIS configuration into this report's own folder (they show timings and
    # trial counts), so a report never reuses figures drawn for another configuration or by the tests.
    stim = out_dir / "design_figures"
    design_figures.generate_all(stim, cfg)
    doc, final = build(cfg, settings, results, figdir, version, stim)
    base = basename or ("SMIT_Research_Report" if final else "Preliminary_Research_Report")
    out_dir.mkdir(parents=True, exist_ok=True)
    files = [
        {"name": to_pdf(doc, out_dir / f"{base}.pdf").name, "label": "PDF"},
        {"name": to_docx(doc, out_dir / f"{base}.docx").name, "label": "DOCX"},
        {"name": to_html(doc, out_dir / f"{base}.html").name, "label": "HTML"},
    ]
    if results:
        files.append({"name": write_results_workbook(results, out_dir / "SMIT_Statistical_Results.xlsx").name, "label": "Statistical results (.xlsx)"})
    return files, final


def _latest_run(db: Session) -> AnalysisRun | None:
    return db.scalar(select(AnalysisRun).where(AnalysisRun.status == "completed").order_by(AnalysisRun.id.desc()))


def generate_report(db: Session) -> GeneratedReport:
    run = _latest_run(db)
    results = run.results_json if run else None
    figdir = Path(run.output_dir) / "figures" if run and run.output_dir else None
    cfg, version = _config_and_version(db, results)
    out = get_settings().outputs_dir / "reports" / datetime.now().strftime("%Y%m%d_%H%M%S")
    files, final = write_report_files(out, cfg, settings_store.get_all(db), results, figdir, version)
    rep = GeneratedReport(kind="final" if final else "preliminary", analysis_run_id=run.id if run else None, output_dir=str(out), files=files)
    db.add(rep)
    db.flush()
    audit(db, "report_generated", entity_type="report", entity_id=str(rep.id), details={"kind": rep.kind, "analysis_run": rep.analysis_run_id})
    db.commit()
    return rep


def generate_presentation(db: Session) -> GeneratedReport:
    run = _latest_run(db)
    results = run.results_json if run else None
    figdir = Path(run.output_dir) / "figures" if run and run.output_dir else None
    cfg, _ = _config_and_version(db, results)
    from ..reports import design_figures
    out = get_settings().outputs_dir / "reports" / ("pres_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    stim = out / "design_figures"
    design_figures.generate_all(stim, cfg)
    p = build_presentation(out / "SMIT_Presentation.pptx", cfg, settings_store.get_all(db), results, figdir, stim)
    rep = GeneratedReport(kind="presentation", analysis_run_id=run.id if run else None, output_dir=str(out),
                          files=[{"name": p.name, "label": "PowerPoint (.pptx)"}])
    db.add(rep)
    db.flush()
    audit(db, "presentation_generated", entity_type="report", entity_id=str(rep.id))
    db.commit()
    return rep
