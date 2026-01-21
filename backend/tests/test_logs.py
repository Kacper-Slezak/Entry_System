from app.db.models import AccessLog, AccessLogStatus
from unittest.mock import patch


def test_log_saved_correctly_on_success(client, mock_db_session, mock_employee):
    """
    Verifies that on success, a log with status GRANTED, reason 'SUCCESS',
    and biometric distance is saved to the database.
    """
    mock_db_session.query().filter().first.return_value = mock_employee

    with patch("app.api.terminal_routes.generate_face_embedding") as mock_gen, \
            patch("app.api.terminal_routes.verify_face") as mock_ver:
        mock_gen.return_value = [0.1, 0.2]
        mock_ver.return_value = (True, 0.15)

        client.post(
            "/api/terminal/access-verify",
            data={"employee_uid": str(mock_employee.uuid)},
            files={"file": ("test.jpg", b"fake_bytes", "image/jpeg")}
        )

    assert mock_db_session.add.called

    saved_log = mock_db_session.add.call_args[0][0]

    assert isinstance(saved_log, AccessLog)
    assert saved_log.status == AccessLogStatus.GRANTED
    assert saved_log.reason == "SUCCESS"
    assert saved_log.employee_id == mock_employee.uuid

    assert saved_log.debug_distance == 0.15


def test_log_saved_correctly_on_face_mismatch(client, mock_db_session, mock_employee):
    """
    Verifies that on face mismatch, DENIED_FACE, 'FACE_MISMATCH',
    and the rejection distance are saved.
    """
    mock_db_session.query().filter().first.return_value = mock_employee

    with patch("app.api.terminal_routes.generate_face_embedding") as mock_gen, \
            patch("app.api.terminal_routes.verify_face") as mock_ver:
        mock_gen.return_value = [0.1, 0.2]

        mock_ver.return_value = (False, 0.85)

        client.post(
            "/api/terminal/access-verify",
            data={"employee_uid": str(mock_employee.uuid)},
            files={"file": ("test.jpg", b"fake_bytes", "image/jpeg")}
        )

    assert mock_db_session.add.called
    saved_log = mock_db_session.add.call_args[0][0]

    assert saved_log.status == AccessLogStatus.DENIED_FACE
    assert saved_log.reason == "FACE_MISMATCH"
    assert saved_log.employee_id == mock_employee.uuid

    assert saved_log.debug_distance == 0.85


def test_log_saved_correctly_on_inactive_employee(client, mock_db_session, mock_employee):
    """
    Verifies that for an inactive employee, DENIED_QR and 'QR_INVALID_OR_INACTIVE' are saved.
    Distance should be None as face verification was skipped.
    """
    mock_employee.is_active = False
    mock_db_session.query().filter().first.return_value = mock_employee

    client.post(
        "/api/terminal/access-verify",
        data={"employee_uid": str(mock_employee.uuid)},
        files={"file": ("test.jpg", b"fake_bytes", "image/jpeg")}
    )

    assert mock_db_session.add.called
    saved_log = mock_db_session.add.call_args[0][0]

    assert saved_log.status == AccessLogStatus.DENIED_QR
    assert saved_log.reason == "QR_INVALID_OR_INACTIVE"
    assert saved_log.employee_id == mock_employee.uuid

    assert saved_log.debug_distance is None


def test_log_saved_correctly_on_multiple_faces(client, mock_db_session, mock_employee):
    """
    Verifies that detecting multiple faces logs DENIED_FACE and 'MULTIPLE_FACES'.
    Distance should be None (error occurs before distance calculation).
    """
    mock_db_session.query().filter().first.return_value = mock_employee

    with patch("app.api.terminal_routes.generate_face_embedding") as mock_gen:
        mock_gen.side_effect = ValueError("MULTIPLE_FACES_DETECTED")

        client.post(
            "/api/terminal/access-verify",
            data={"employee_uid": str(mock_employee.uuid)},
            files={"file": ("test.jpg", b"fake_bytes", "image/jpeg")}
        )

    assert mock_db_session.add.called
    saved_log = mock_db_session.add.call_args[0][0]

    assert saved_log.status == AccessLogStatus.DENIED_FACE
    assert saved_log.reason == "MULTIPLE_FACES"
    assert saved_log.employee_id == mock_employee.uuid

    assert saved_log.debug_distance is None


def test_log_saved_on_invalid_uuid_format(client, mock_db_session):
    """
    Verifies that providing an invalid UUID format logs DENIED_QR and 'QR_INVALID_FORMAT'.
    Distance should be None.
    """
    client.post(
        "/api/terminal/access-verify",
        data={"employee_uid": "not-a-valid-uuid"},
        files={"file": ("test.jpg", b"fake_bytes", "image/jpeg")}
    )

    assert mock_db_session.add.called
    saved_log = mock_db_session.add.call_args[0][0]

    assert saved_log.status == AccessLogStatus.DENIED_QR
    assert saved_log.reason == "QR_INVALID_FORMAT"
    assert saved_log.employee_id is None

    assert saved_log.debug_distance is None
    