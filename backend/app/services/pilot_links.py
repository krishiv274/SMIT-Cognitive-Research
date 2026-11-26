"""Server-side revocation of pilot links.

Pilot links carry a signed token valid for 6 hours. Revoking stores a timestamp;
any pilot token issued before it is rejected, wherever the link was copied to.
"""
from __future__ import annotations

import time

from sqlalchemy.orm import Session

from ..models import AppSetting

KEY = "pilot_links_revoked_at"
PILOT_TTL_S = 6 * 3600


def revoked_at(db: Session) -> float:
    row = db.get(AppSetting, KEY)
    try:
        return float(row.value) if row and row.value else 0.0
    except ValueError:
        return 0.0


def revoke_all(db: Session) -> float:
    now = time.time()
    row = db.get(AppSetting, KEY)
    if row is None:
        db.add(AppSetting(key=KEY, value=str(now)))
    else:
        row.value = str(now)
    return now


def issued_at(body: dict) -> float:
    return float(body.get("iat") or (body.get("exp", 0) - PILOT_TTL_S))


def is_revoked(db: Session, body: dict) -> bool:
    return issued_at(body) < revoked_at(db)
