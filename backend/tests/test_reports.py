import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import models
from backend.app.db.models import AccessLogStatus

client = TestClient(app)


@pytest.fixture
def sample_data(mock_db_session):
    # 1. Create sample data
    employee = models.Employee(
        name="Report Test User",
        email="report@test.com",
        is_active=True,
        embedding=None
    )
    import uuid
    employee.uuid = uuid.uuid4()

    # We add to the mock just for consistency, though it doesn't store state
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

    # 2. ROBUST MOCK CONFIGURATION (The Fix)

    # We grab the mock object that simulates the query
    query_mock = mock_db_session.query.return_value

    # CRITICAL: We tell the mock "No matter what method is called, return YOURSELF"
    # This prevents the chain from breaking when .join() or .order_by() is called.
    query_mock.join.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.order_by.return_value = query_mock
    query_mock.limit.return_value = query_mock

    # Finally, when .all() is called on this persistent mock, return our data
    query_mock.all.return_value = [log_granted, log_denied]

    # Save specifically for the filtering test usage
    mock_db_session.denied_log = log_denied

    return employee


def test_get_logs_json(sample_data, mock_db_session):
    """
    Tests the GET /admin/logs endpoint (JSON table view).
    """
    response = client.get("/admin/logs")

    assert response.status_code == 200
    data = response.json()

    # Now chaining works, so we should see data
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
    # Override the .all() return value JUST for this test case
    # Since we configured filter() to return the query_mock, calling .all() checks this value
    mock_db_session.query.return_value.all.return_value = [mock_db_session.denied_log]

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

    assert (
            "ID;Date;Hour;Status;Reason;Worker Name;Email" in content
            or "ID,Date,Hour,Status,Reason,Worker Name,Email" in content
    )

    assert "Report Test User" in content
    assert "Face does not match" in content
