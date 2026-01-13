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
    # 2. THE NUCLEAR SOLUTION: Custom Mock Class
    # ==========================================
    class MockQuery:
        def __init__(self, items):
            self.items = items

        def all(self):
            return self.items

        def first(self):
            return self.items[0] if self.items else None

        def count(self):
            return len(self.items)

        # The magic: any other attribute access returns a function that returns self
        # This handles .filter(), .order_by(), .join(), .limit(), etc. automatically
        def __getattr__(self, name):
            return lambda *args, **kwargs: self

    # We force the db.query to return an instance of our MockQuery with our data
    mock_db_session.query.side_effect = lambda *args, **kwargs: MockQuery([log_granted, log_denied])

    # Save references for use in tests
    mock_db_session.all_logs = [log_granted, log_denied]
    mock_db_session.denied_log = log_denied
    # Save the class so we can use it in filtering test
    mock_db_session.MockQueryClass = MockQuery

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
    # Override the side_effect to return only denied logs
    mock_db_session.query.side_effect = lambda *args, **kwargs: mock_db_session.MockQueryClass(
        [mock_db_session.denied_log])

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
