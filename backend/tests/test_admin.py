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
    """
    Test the successful update of an employee's profile including biometrics.

    GIVEN: An existing employee and a new reference photo.
    WHEN: A PUT request is sent to the administration update endpoint.
    THEN: The system should update the name, email, and generate a new embedding.
    """
    # First call: find the employee to update
    # Second call: check if the new email is already in use (should return None)
    mock_db_session.query().filter().first.side_effect = [mock_employee, None]

    with patch("app.api.admin_routes.generate_face_embedding") as mock_emb, \
         patch("app.api.admin_routes.send_qr_code_via_email") as mock_email:
        # Mocking the 512-D vector return value from the biometric service
        mock_emb.return_value = [0.9, 0.8, 0.7]
        # Mocking email sending to do nothing (just pass)
        mock_email.return_value = None

        response = client.put(
            f"/admin/employees/{mock_employee.uuid}",
            data={"name": "New Name", "email": "new_email@test.com"},
            files={"photo": ("new_face.jpg", b"fake_image_bytes", "image/jpeg")}
        )

    # Assertions to verify correct behavior
    assert response.status_code == 200
    assert response.json()["message"] == "Updated successfully"
    assert mock_employee.name == "New Name"
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
