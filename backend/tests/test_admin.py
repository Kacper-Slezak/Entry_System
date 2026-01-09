import pytest
import sys
import os
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient

# 1. SETUP PATH
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

# 2. SETUP ENV VARS
os.environ["MAIL_FROM"] = "test@example.com"
os.environ["MAIL_USERNAME"] = "test@example.com"
os.environ["MAIL_PASSWORD"] = "test_password"
os.environ["MAIL_PORT"] = "587"
os.environ["MAIL_SERVER"] = "smtp.test.com"

# 3. MOCK SIDE EFFECTS DURING IMPORT
# We use a context manager to mock functions that run at the top-level of main.py
with patch("app.db.models.Base.metadata.create_all"), \
     patch("app.main.create_default_admin"):

    # Now it is safe to import the app
    from app.main import app
    from app.db.session import get_db

# 4. DATABASE OVERRIDE
# This handles the DB calls that happen inside your API routes
def override_get_db():
    try:
        db = MagicMock()
        # Mock specific DB methods used in your routes
        db.commit = MagicMock()
        db.refresh = MagicMock()
        db.query = MagicMock()
        yield db
    finally:
        pass

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_health_check():
    response = client.get("/admin/health")
    assert response.status_code == 200
    assert response.json() == {"200": "OK"}

@patch("app.api.admin_routes.generate_face_embedding")
@patch("app.api.admin_routes.send_qr_code_via_email", new_callable=AsyncMock)
def test_create_employee_success(mock_send_email, mock_embedding):
    # Mock AI response
    mock_embedding.return_value = [0.1, 0.2, 0.3, 0.4]

    # Mock Data
    fake_photo = b"fake_image_bytes"
    files = {"photo": ("face.jpg", fake_photo, "image/jpeg")}
    data = {
        "name": "Jan Kowalski",
        "email": "jan@test.pl"
    }

    response = client.post("/admin/create_employee", data=data, files=files)

    assert response.status_code == 200
    assert response.json() == {"message": "Employee created successfully"}
    mock_embedding.assert_called_once()
    mock_send_email.assert_called_once()

    # Verify email was sent to correct recipient
    args, _ = mock_send_email.call_args
    assert args[0] == "jan@test.pl"
