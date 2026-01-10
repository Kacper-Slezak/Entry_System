import pytest
from unittest.mock import patch, AsyncMock
from app.db.models import Employee

@patch("app.api.admin_routes.generate_face_embedding")
@patch("app.api.admin_routes.send_qr_code_via_email", new_callable=AsyncMock)
def test_create_employee_success(mock_send_email, mock_embedding, client, mock_db_session):
    mock_embedding.return_value = [0.1, 0.2, 0.3]

    files = {"photo": ("face.jpg", b"fake_data", "image/jpeg")}
    data = {"name": "Jan Kowalski", "email": "jan@test.pl"}

    response = client.post("/admin/create_employee", data=data, files=files)


    assert response.status_code == 200
    assert response.json()["message"] == "Employee created successfully"


    assert mock_db_session.add.called
    assert mock_db_session.commit.called
