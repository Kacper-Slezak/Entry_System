import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import get_db

# 1. Database override
# Instead of connecting to the real Postgres, we substitute a mock (MagicMock)
def override_get_db():
    try:
        db = MagicMock()
        # Pretend that commit and refresh work and do nothing
        db.commit = MagicMock()
        db.refresh = MagicMock()
        yield db
    finally:
        pass

# Override the dependency in the FastAPI application
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
