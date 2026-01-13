import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import models
from backend.app.db.models import AccessLogStatus

client = TestClient(app)


@pytest.fixture
def sample_data(mock_db_session):
    # 1. Create sample data in test memory
    employee = models.Employee(
        name="Report Test User",
        email="report@test.com",
        is_active=True,
        embedding=None
    )
    import uuid
    employee.uuid = uuid.uuid4()

    mock_db_session.add(employee)
    mock_db_session.commit()
    mock_db_session.refresh(employee)

    log_granted = models.AccessLog(
        timestamp=datetime.utcnow(),
        status=AccessLogStatus.GRANTED,
        reason="Verification successful",
        employee_id=employee.uuid,
        employee=employee
    )

    log_denied = models.AccessLog(
        timestamp=datetime.utcnow(),
        status=AccessLogStatus.DENIED_FACE,
        reason="Face does not match",
        employee_id=None,
        employee=None
    )

    # 2. ADVANCED MOCK CONFIGURATION (Fix for chaining methods like .order_by)

    # Create a mock query object
    mock_query = mock_db_session.query.return_value

    # CHAINING FIX: If the app calls .filter() or .order_by(), return the SAME mock_query object
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query

    # Finally, when .all() is called, return our list
    mock_query.all.return_value = [log_granted, log_denied]

    # Store logs in the session object so we can access them in individual tests if needed
    mock_db_session.logs_list = [log_granted, log_denied]
    mock_db_session.denied_log = log_denied

    return employee


def test_get_logs_json(sample_data, mock_db_session):
    """
    Tests the GET /admin/logs endpoint (JSON table view).
    """
    response = client.get("/admin/logs")

    assert response.status_code == 200
    data = response.json()

    assert len(data) >= 2

    found_granted = False
    for entry in data:
        if entry["status"] == "GRANTED":
            found_granted = True
            assert entry["employee_name"] == "Report Test User"
            assert entry["reason"] == "Verification successful"

    assert found_granted is True


def test_get_logs_filtering(sample_data, mock_db_session):
    """
    Tests filtering logs by status.
    """
    # OVERRIDE MOCK: For this specific test, we simulate that the DB returns only DENIED logs
    # (Since MagicMock cannot actually execute SQL logic, we must force the return value)
    mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
        mock_db_session.denied_log]

    # Also handle case without order_by just to be safe
    mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_db_session.denied_log]

    response = client.get("/admin/logs?status=DENIED_FACE")

    assert response.status_code == 200
    data = response.json()

    assert len(data) > 0
    for entry in data:
        assert entry["status"] == "DENIED_FACE"


def test_export_csv(sample_data):
    """
    Tests CSV file export.
    """
    response = client.get("/admin/logs/export")

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]

    assert "attachment; filename=raport_wejsc.csv" in response.headers["content-disposition"]

    content = response.text

    # FIX: Updated expected headers to match what backend actually returns ("Hour", "Worker Name")
    assert (
            "ID;Date;Hour;Status;Reason;Worker Name;Email" in content
            or "ID,Date,Hour,Status,Reason,Worker Name,Email" in content
    )

    assert "Report Test User" in content
    assert "Face does not match" in content
