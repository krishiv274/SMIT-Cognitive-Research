"""Researcher authentication and small crypto helpers (stdlib only)."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time

from fastapi import Depends, Header, HTTPException, status

from .settings import get_settings


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def sign_token(payload: dict, ttl_seconds: int) -> str:
    body = dict(payload, exp=int(time.time()) + ttl_seconds)
    raw = _b64(json.dumps(body, separators=(",", ":")).encode())
    sig = _b64(hmac.new(get_settings().secret_key.encode(), raw.encode(), hashlib.sha256).digest())
    return f"{raw}.{sig}"


def verify_token(token: str, expected_kind: str) -> dict:
    try:
        raw, sig = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Malformed token") from exc
    good = _b64(hmac.new(get_settings().secret_key.encode(), raw.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(good, sig):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    body = json.loads(_unb64(raw))
    if body.get("exp", 0) < time.time():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired — please log in again")
    if body.get("kind") != expected_kind:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong token type")
    return body


def check_admin_password(password: str) -> bool:
    return hmac.compare_digest(password.encode(), get_settings().admin_password.encode())


def issue_admin_token() -> str:
    return sign_token({"kind": "admin", "nonce": secrets.token_hex(8)}, get_settings().token_ttl_hours * 3600)


def require_admin(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Researcher login required")
    return verify_token(authorization.split(" ", 1)[1].strip(), "admin")


AdminDep = Depends(require_admin)


def new_session_token() -> tuple[str, str]:
    tok = secrets.token_urlsafe(32)
    return tok, hashlib.sha256(tok.encode()).hexdigest()


def check_session_token(token: str | None, token_hash: str | None) -> bool:
    if not token or not token_hash:
        return False
    return hmac.compare_digest(hashlib.sha256(token.encode()).hexdigest(), token_hash)


def email_hash(email: str) -> str:
    norm = email.strip().lower()
    return hmac.new(get_settings().email_pepper.encode(), norm.encode(), hashlib.sha256).hexdigest()
