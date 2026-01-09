import pytest
import sys
import os
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient

# 1. SETUP PATH
# Ensure the backend directory is in the python path
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

# 2. SETUP ENV VARS
# These must be set BEFORE importing app.main to pass validation in utils.py
os.environ["MAIL_FROM"] = "test@example.com"
os.environ["MAIL_USERNAME"] = "test@example.com"
os.environ["MAIL_PASSWORD"] = "test_password"
os.environ["MAIL_PORT"] = "587"
os.environ["MAIL_SERVER"] = "smtp.test.com"

# 3. MOCK DB INIT & IMPORT APP
# We mock 'create_all' to prevent app.main from trying to connect
# to a non-existent database during the import.
with patch("app.db.models.Base.metadata.create_all"), \
     patch("app.utils.create_default_admin"):
    from app.main import app
    from app.db.session import get_db

# 4. Database override
# Instead of connecting to the real Postgres, we substitute a mock
def override_get_db():
    try:
        db = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        yield db
    finally:
        pass

# Apply the override
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_health_check():
    """
    Checks if the health endpoint returns 200 OK.
    """
    response = client.get("/admin/health")
    assert response.status_code == 200
    assert response.json() == {"200": "OK"}

# Patch (mock) external functions to avoid running AI or sending emails
@patch("app.api.admin_routes.generate_face_embedding")
@patch("app.api.admin_routes.send_qr_code_via_email", new_callable=AsyncMock)
def test_create_employee_success(mock_send_email, mock_embedding):
    """
    Tests successful employee creation.
    Simulates DeepFace behavior and email sending.
    """
    # Set what our "fake" AI should return
    mock_embedding.return_value = [0.1, 0.2, 0.3, 0.4]  # Example vector

    # Test data (fake photo and form)
    fake_photo = b"fake_image_bytes"
    files = {"photo": ("face.jpg", fake_photo, "image/jpeg")}
    data = {
        "name": "Jan Kowalski",
        "email": "jan@test.pl"
    }

    # Execute request to the endpoint
    response = client.post("/admin/create_employee", data=data, files=files)

    # Assertions
    # 1. Is the status 200 OK?
    assert response.status_code == 200

    # 2. Did we get the correct JSON response?
    assert response.json() == {"message": "Employee created successfully"}

    # 3. Was the AI function called exactly once?
    mock_embedding.assert_called_once()

    # 4. Was the email sending function called?
    mock_send_email.assert_called_once()

    # Check if the email was sent to the correct address
    args, _ = mock_send_email.call_args
    assert args[0] == "jan@test.pl"
