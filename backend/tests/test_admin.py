import pytest
from unittest.mock import patch, MagicMock
import uuid

def test_get_all_employees(client, mock_db_session, mock_employee):
    """Test for retrieving the list of employees."""
    mock_db_session.query().all.return_value = [mock_employee]

    response = client.get("/admin/employees")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["email"] == mock_employee.email

def test_update_employee_profile_with_photo(client, mock_db_session, mock_employee):
    """Test for updating employee data along with a new photo."""
    mock_db_session.query().filter().first.return_value = mock_employee

    with patch("app.api.admin_routes.generate_face_embedding") as mock_emb:
        mock_emb.return_value = [0.9, 0.8, 0.7]

        response = client.put(
            f"/admin/employees/{mock_employee.uuid}",
            data={"name": "Nowe Imie", "email": "nowy@test.pl"},
            files={"photo": ("new.jpg", b"new_photo_data", "image/jpeg")}
        )

    assert response.status_code == 200
    assert mock_employee.name == "Nowe Imie"
    assert mock_employee.embedding == [0.9, 0.8, 0.7]
    assert mock_db_session.commit.called

def test_delete_employee_success(client, mock_db_session, mock_employee):
    """Test for deleting an employee."""
    mock_db_session.query().filter().first.return_value = mock_employee

    response = client.delete(f"/admin/employees/{mock_employee.uuid}")

    assert response.status_code == 200
    assert response.json()["message"] == "Employee deleted successfully"
    assert mock_db_session.delete.called
    assert mock_db_session.commit.called

def test_delete_employee_not_found(client, mock_db_session):
    """Test for deleting a non-existent employee (404)."""
    mock_db_session.query().filter().first.return_value = None
    random_uuid = uuid.uuid4()

    response = client.delete(f"/admin/employees/{random_uuid}")

    assert response.status_code == 404
