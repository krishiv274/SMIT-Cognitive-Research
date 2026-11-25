"""Audit logging. Never put email addresses or other identifying data in details."""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import AuditLog


def audit(db: Session, action: str, *, actor: str = "researcher", entity_type: str | None = None,
          entity_id: str | None = None, details: dict | None = None) -> None:
    db.add(AuditLog(actor=actor, action=action, entity_type=entity_type,
                    entity_id=str(entity_id) if entity_id is not None else None, details=details or {}))
