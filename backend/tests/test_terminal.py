import pytest
from unittest.mock import patch, MagicMock
from app.db.models import AccessLogStatus

def test_verify_access_success(client, mock_db_session, mock_employee):
    """Test for full success: QR is valid and face matches."""
    mock_db_session.query().filter().first.return_value = mock_employee

    with patch("app.api.terminal_routes.generate_face_embedding") as mock_gen, \
         patch("app.api.terminal_routes.verify_face") as mock_ver:

        mock_gen.return_value = [0.1, 0.2]
        mock_ver.return_value = (True, 0.15) # (is_match, distance)

        response = client.post(
            "/api/terminal/access-verify",
            data={"employee_uid": str(mock_employee.uuid)},
            files={"file": ("test.jpg", b"image_content", "image/jpeg")}
        )

    assert response.status_code == 200
    assert response.json()["access"] == "GRANTED"
    assert response.json()["name"] == mock_employee.name
    assert mock_db_session.add.called


def test_verify_access_face_mismatch(client, mock_db_session, mock_employee):
    """Test situation: QR is correct, but face of another person (mismatch)."""
    mock_db_session.query().filter().first.return_value = mock_employee

    with patch("app.api.terminal_routes.generate_face_embedding") as mock_gen, \
         patch("app.api.terminal_routes.verify_face") as mock_ver:

        mock_gen.return_value = [0.1, 0.2]
        mock_ver.return_value = (False, 0.85)

        response = client.post(
            "/api/terminal/access-verify",
            data={"employee_uid": str(mock_employee.uuid)},
            files={"file": ("test.jpg", b"image_content", "image/jpeg")}
        )

    assert response.json()["access"] == "DENIED"
    assert response.json()["reason"] == "FACE_MISMATCH"


def test_verify_access_no_face_detected(client, mock_db_session, mock_employee):
    """Test when no face was detected in the photo."""
    mock_db_session.query().filter().first.return_value = mock_employee

    with patch("app.api.terminal_routes.generate_face_embedding", return_value=None):
        response = client.post(
            "/api/terminal/access-verify",
            data={"employee_uid": str(mock_employee.uuid)},
            files={"file": ("test.jpg", b"image_content", "image/jpeg")}
        )

    assert response.json()["reason"] == "NO_FACE_DETECTED"
