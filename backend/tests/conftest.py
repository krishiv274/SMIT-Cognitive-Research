"""Test configuration: every test session uses a fresh TEMPORARY data directory.

The research database (data/smit.db) is never touched by tests.
"""
import os
import tempfile
from pathlib import Path

import pytest

_TMP = Path(tempfile.mkdtemp(prefix="smit_test_"))
os.environ["SMIT_DATA_DIR"] = str(_TMP)
os.environ["SMIT_DATABASE_URL"] = f"sqlite:///{_TMP / 'test.db'}"
os.environ["SMIT_ADMIN_PASSWORD"] = "test-password"
os.environ["SMIT_SECRET_KEY"] = "test-secret"
os.environ["SMIT_ALLOW_SYNTHETIC_IMPORTS"] = "true"
os.environ["SMIT_FRONTEND_DIST"] = str(_TMP / "no-frontend")

from app.db import Base, get_engine, reset_engine  # noqa: E402
from app.settings import get_settings  # noqa: E402

get_settings.cache_clear()
ARTIFACTS = Path(__file__).resolve().parent / "artifacts"


@pytest.fixture()
def fresh_db():
    """Drop and recreate all tables (isolation between tests)."""
    from app import models  # noqa: F401

    reset_engine()
    eng = get_engine()
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    yield
    reset_engine()


@pytest.fixture()
def client(fresh_db):
    from fastapi.testclient import TestClient

    from app.main import create_app

    with TestClient(create_app()) as c:
        yield c


@pytest.fixture()
def admin_headers(client):
    tok = client.post("/api/admin/login", json={"password": "test-password"}).json()["token"]
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture()
def db(fresh_db):
    from app.db import session_factory
    from app.services.configs import ensure_default_config

    s = session_factory()()
    ensure_default_config(s)
    yield s
    s.close()


@pytest.fixture(scope="session")
def artifacts():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    return ARTIFACTS
