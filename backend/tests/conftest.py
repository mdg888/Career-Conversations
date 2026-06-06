import os
import pytest
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

os.environ.setdefault("OPENAI_API_KEY", "test-key")


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    """Provide a temporary isolated database for each test."""
    from backend.src import db
    import backend.src.db.database as db_module

    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_module, "_DB_PATH", db_path)
    db_module.init_db(db_path)
    return db_path


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Provide a temporary data directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def client(tmp_db):
    """Provide a test client for the FastAPI app."""
    from backend.src.api.main import app
    return TestClient(app)
