"""Editable study settings (title page, institutional details, pilot notes)."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import AppSetting
from .audit import audit

DEFAULT_SETTINGS: dict[str, str] = {
    "university_name": "[UNIVERSITY NAME]",
    "department": "[DEPARTMENT]",
    "course_name": "Cognitive Psychology",
    "student_names": "[STUDENT NAMES]",
    "student_ids": "[STUDENT IDS]",
    "professor_name": "[PROFESSOR NAME]",
    "submission_date": "[SUBMISSION DATE]",
    "researcher_contact": "[RESEARCHER CONTACT EMAIL]",
    "supervisor_contact": "[SUPERVISOR CONTACT EMAIL]",
    "ethics_statement": (
        "This is a student research study conducted for a Cognitive Psychology course assignment. "
        "[State the actual ethics status here. Do not claim institutional ethics approval unless it has been granted.]"
    ),
    "withdrawal_deadline": "[DATE — e.g. the report submission date]",
    "data_storage_statement": "Data are stored locally on the researchers' computer and are not sent to third-party services.",
    "retention_statement": "[e.g. Contact details are deleted at the end of the semester; de-identified data are kept for one year.]",
    "apparatus": "[Computer model, operating system, browser and version, monitor size and refresh rate, wired keyboard model]",
    "pilot_observations": "",
    "pilot_design_changes": "",
    "deviations_from_plan": "",
    "recruitment_description": "[Describe how participants were recruited, e.g. class announcement, dates of data collection]",
}

PUBLIC_KEYS = {
    "university_name", "department", "course_name", "student_names", "professor_name", "researcher_contact",
    "supervisor_contact", "ethics_statement", "withdrawal_deadline", "data_storage_statement", "retention_statement",
}


def get_all(db: Session) -> dict[str, str]:
    out = dict(DEFAULT_SETTINGS)
    for row in db.scalars(select(AppSetting)).all():
        if row.key in out and row.value is not None:
            out[row.key] = row.value
    return out


def get_public(db: Session) -> dict[str, str]:
    allv = get_all(db)
    return {k: v for k, v in allv.items() if k in PUBLIC_KEYS}


def update(db: Session, values: dict[str, str]) -> dict[str, str]:
    changed = []
    for k, v in values.items():
        if k not in DEFAULT_SETTINGS:
            continue
        v = (v or "")[:20000]
        row = db.get(AppSetting, k)
        if row is None:
            db.add(AppSetting(key=k, value=v))
        else:
            row.value = v
        changed.append(k)
    if changed:
        audit(db, "settings_updated", entity_type="settings", details={"keys": changed})
    return get_all(db)


def is_placeholder(value: str) -> bool:
    return (not value) or value.strip().startswith("[")
