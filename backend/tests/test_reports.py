import pytest
from unittest.mock import MagicMock
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

    # ==========================================
    # 2. ROBUST MOCK CONFIGURATION
    # ==========================================

    # Create the master query mock object
    query_mock = MagicMock()

    # Configure chaining: ensure all common SQLAlchemy methods return the same mock object
    query_mock.join.return_value = query_mock
    query_mock.outerjoin.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.filter_by.return_value = query_mock
    query_mock.order_by.return_value = query_mock
    query_mock.group_by.return_value = query_mock
    query_mock.limit.return_value = query_mock
    query_mock.offset.return_value = query_mock
    query_mock.distinct.return_value = query_mock
    query_mock.options.return_value = query_mock

    # Default behavior: return both logs
    query_mock.all.return_value = [log_granted, log_denied]

    # KEY FIX: Attach this specific mock to the session so tests can access it
    mock_db_session.backend_query = query_mock

    # Force db.query(...) to always return our configured query_mock
    mock_db_session.query.side_effect = lambda *args, **kwargs: query_mock

    # Save references for use in tests
    mock_db_session.denied_log = log_denied

    return employee


def test_get_logs_json(sample_data, mock_db_session):
    """
    Tests the GET /admin/logs endpoint (JSON table view).
    """
    response = client.get("/admin/logs")

    assert response.status_code == 200
    data = response.json()

    # Should return 2 records
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
    # CRITICAL FIX: We modify the SPECIFIC mock object stored in the fixture
    # instead of trying to patch mock_db_session.query.return_value
    mock_db_session.backend_query.all.return_value = [mock_db_session.denied_log]

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
