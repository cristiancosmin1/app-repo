import os

import pytest
from fastapi.testclient import TestClient


os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["OTEL_SDK_DISABLED"] = "true"


from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client
