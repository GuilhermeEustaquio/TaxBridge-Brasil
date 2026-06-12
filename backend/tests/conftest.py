import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_tmpdir = tempfile.mkdtemp(prefix="taxbridge-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmpdir}/test.db"
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"
os.environ["AUTO_CREATE_TABLES"] = "true"
os.environ["AUTH_RATE_LIMIT_PER_MINUTE"] = "1000"
os.environ["ANTHROPIC_API_KEY"] = ""

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def auth_headers(client) -> dict:
    """Registra organização de teste e devolve headers autenticados (dono_conta)."""
    response = client.post("/api/v1/auth/register", json={
        "organization_name": "Org Teste Ltda",
        "name": "Usuária Dona",
        "email": "dona@teste.com.br",
        "password": "SenhaForte@123",
        "lgpd_consent": True,
    })
    assert response.status_code == 201, response.text
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}
