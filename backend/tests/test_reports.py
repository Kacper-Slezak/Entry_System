import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import models
from backend.app.db.models import AccessLogStatus

client = TestClient(app)


@pytest.fixture
def sample_data(mock_db_session):
    employee = models.Employee(
        name="Report Test User",
        email="report@test.com",
        is_active=True,
        embedding=None
    )
    mock_db_session.add(employee)
    mock_db_session.commit()
    mock_db_session.refresh(employee)

    log_granted = models.AccessLog(
        timestamp=datetime.utcnow(),
        status=AccessLogStatus.GRANTED,
        reason="Verification successful",
        employee_id=employee.uuid
    )

    log_denied = models.AccessLog(
        timestamp=datetime.utcnow(),
        status=AccessLogStatus.DENIED_FACE,
        reason="Face does not match",
        employee_id=None
    )

    mock_db_session.add(log_granted)
    mock_db_session.add(log_denied)
    mock_db_session.commit()

    return employee  # Return employee in case it is needed in assertions


def test_get_logs_json(sample_data, mock_db_session):
    """
    Tests the GET /admin/logs endpoint (JSON table view).
    Verifies correct data formatting and checks whether the employee name is present.
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


def test_get_logs_filtering(sample_data):
    """
    Tests filtering logs by status.
    """
    response = client.get("/admin/logs?status=DENIED_FACE")

    assert response.status_code == 200
    data = response.json()

    # There should be at least one entry, and each must have DENIED_FACE status
    assert len(data) > 0
    for entry in data:
        assert entry["status"] == "DENIED_FACE"


def test_export_csv(sample_data):
    """
    Tests CSV file export.
    Verifies HTTP headers and checks whether the file content contains data.
    """
    response = client.get("/admin/logs/export")

    # 1. Check response status and file type
    assert response.status_code == 200
    # Verify that the browser receives information that this is a CSV file
    assert "text/csv" in response.headers["content-type"]
    assert "attachment; filename=access_report.csv" in response.headers["content-disposition"]

    # 2. Check CSV file content
    content = response.text

    # Are column headers present?
    assert (
        "ID;Date;Time;Status;Reason;Employee Name;Email" in content
        or "ID,Date,Time,Status,Reason,Employee Name,Email" in content
    )

    # Is employee data present in the file?
    assert "Report Test User" in content
    assert "Face does not match" in content
