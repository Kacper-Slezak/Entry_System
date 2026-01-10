import pytest
import sys
import os
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.core.security import get_current_active_admin
from app.db.models import Admin

@pytest.fixture
def mock_admin():
    return Admin(id=1, username="test_admin", is_active=True)

@pytest.fixture(autouse=True)
def setup_dependency_overrides(mock_admin):
    async def override_get_admin():
        return mock_admin

    app.dependency_overrides[get_current_active_admin] = override_get_admin
    yield
    app.dependency_overrides = {}

@pytest.fixture
def client():
    return TestClient(app)
