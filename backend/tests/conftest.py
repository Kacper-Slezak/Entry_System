import pytest
import sys
import os
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

os.environ["MAIL_USERNAME"] = "test_user"
os.environ["MAIL_PASSWORD"] = "test_password"
os.environ["MAIL_FROM"] = "admin@test.com"
os.environ["MAIL_PORT"] = "587"
os.environ["MAIL_SERVER"] = "localhost"
os.environ["MAIL_FROM_NAME"] = "Test System"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.core.security import get_current_active_admin
from app.db.session import get_db
from app.db.models import Admin

@pytest.fixture
def mock_admin():
    return Admin(id=1, username="test_admin", is_active=True)

@pytest.fixture
def mock_db_session():
    session = MagicMock()
    session.refresh.return_value = None
    return session

@pytest.fixture(autouse=True)
def setup_dependency_overrides(mock_admin, mock_db_session):
    async def override_get_admin():
        return mock_admin

    def override_get_db():
        yield mock_db_session

    app.dependency_overrides[get_current_active_admin] = override_get_admin
    app.dependency_overrides[get_db] = override_get_db

    yield

    app.dependency_overrides = {}

@pytest.fixture
def client():
    return TestClient(app)
