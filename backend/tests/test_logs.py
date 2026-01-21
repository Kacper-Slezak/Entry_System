from app.db.models import AccessLog, AccessLogStatus
from unittest.mock import patch


def test_log_saved_correctly_on_success(client, mock_db_session, mock_employee):
    """
    Sprawdza, czy w przypadku sukcesu do bazy trafia log ze statusem GRANTED i reason 'SUCCESS'.
    """
    mock_db_session.query().filter().first.return_value = mock_employee

    with patch("app.api.terminal_routes.generate_face_embedding") as mock_gen, \
            patch("app.api.terminal_routes.verify_face") as mock_ver:
        mock_gen.return_value = [0.1, 0.2]
        mock_ver.return_value = (True, 0.15)  # Face match

        client.post(
            "/api/terminal/access-verify",
            data={"employee_uid": str(mock_employee.uuid)},
            files={"file": ("test.jpg", b"fake_bytes", "image/jpeg")}
        )

    # 1. Sprawdź czy db.add zostało wywołane
    assert mock_db_session.add.called

    # 2. Pobierz argument przekazany do db.add (czyli nasz obiekt logu)
    # call_args[0] to argumenty pozycyjne, [0] to pierwszy argument
    saved_log = mock_db_session.add.call_args[0][0]

    # 3. Asercje na polach obiektu
    assert isinstance(saved_log, AccessLog)
    assert saved_log.status == AccessLogStatus.GRANTED
    assert saved_log.reason == "SUCCESS"
    assert saved_log.employee_id == mock_employee.uuid


def test_log_saved_correctly_on_face_mismatch(client, mock_db_session, mock_employee):
    """
    Sprawdza, czy przy niezgodności twarzy zapisuje się DENIED_FACE i 'FACE_MISMATCH'.
    """
    mock_db_session.query().filter().first.return_value = mock_employee

    with patch("app.api.terminal_routes.generate_face_embedding") as mock_gen, \
            patch("app.api.terminal_routes.verify_face") as mock_ver:
        mock_gen.return_value = [0.1, 0.2]
        mock_ver.return_value = (False, 0.85)  # Mismatch

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
    # Opcjonalnie sprawdź czy zapisał się debug_distance, jeśli masz to w modelu
    # assert saved_log.debug_distance == 0.85


def test_log_saved_correctly_on_inactive_employee(client, mock_db_session, mock_employee):
    """
    Sprawdza, czy dla nieaktywnego pracownika zapisuje się DENIED_QR i 'QR_INVALID_OR_INACTIVE'.
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
    # Tutaj logika mówi: employee_id=uid_obj if employee else None.
    # Skoro employee został znaleziony (ale jest nieaktywny), ID powinno być w logu.
    assert saved_log.employee_id == mock_employee.uuid


def test_log_saved_correctly_on_multiple_faces(client, mock_db_session, mock_employee):
    """
    Sprawdza, czy wykrycie wielu twarzy loguje DENIED_FACE i 'MULTIPLE_FACES'.
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


def test_log_saved_on_invalid_uuid_format(client, mock_db_session):
    """
    Sprawdza, czy podanie błędnego formatu UUID loguje DENIED_QR i 'QR_INVALID_FORMAT'.
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
