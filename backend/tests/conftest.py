import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('DB_PATH', str(tmp_path / 'test.db'))
    with TestClient(app) as test:
        yield test
