import sys
from pathlib import Path

# Make the inner app folder importable when pytest runs from the repo root.
APP_ROOT = Path(__file__).resolve().parent.parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))


import pytest

from app import app as flask_app
from database import db as db_module


@pytest.fixture
def app(tmp_path, monkeypatch):
    """A Flask app instance pointed at a fresh on-disk SQLite DB per test.

    Using tmp_path (a pytest-provided temp directory) keeps each test
    isolated from the real `instance/spendly.db` and from other tests.
    We monkey-patch the SECRET_KEY to a fixed value so sessions behave
    deterministically.

    The app's module-level `init_db()` and `seed_db()` calls already ran
    at import time against the real DB — we re-run them against the
    temp DB by setting `DATABASE` before opening an app context.
    """
    db_path = tmp_path / "test_spendly.db"
    flask_app.config.update(
        TESTING=True,
        DATABASE=str(db_path),
        SECRET_KEY="test-secret",
    )

    with flask_app.app_context():
        db_module.init_db()
        db_module.seed_db()

    yield flask_app


@pytest.fixture
def client(app):
    """A Flask test client."""
    return app.test_client()


@pytest.fixture
def auth_user(client):
    """Register a fresh user and return their credentials."""
    client.post(
        "/register",
        data={"name": "Test User", "email": "test@example.com", "password": "password123"},
    )
    return {"email": "test@example.com", "password": "password123"}
