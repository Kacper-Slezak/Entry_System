from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Response, Depends, HTTPException, status, Form, UploadFile, File, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.utils import generate_qr_code, send_qr_code_via_email
from app.services.biometric_service import generate_face_embedding
from app.db.models import Employee, Admin
from app.db.session import get_db
from io import BytesIO
from typing import List, Optional
from pydantic import BaseModel
import uuid

from app.core import security
from app import schemas


adminRouter = APIRouter(prefix="/admin", tags=["admin"])

@adminRouter.get("/health")
async def health_check():
    return {200: "OK"}

@adminRouter.get("/qr_test/{uuid_value}")
async def qr_test(uuid_value: str, email: str = None):
    """
    Generates a QR code for the given UUID value.
    On address /admin/qr_test/{uuid_value} you will get a QR code image.
    """
    qr_stream = generate_qr_code(uuid_value)

    if email:
        qr_for_email = BytesIO(qr_stream.getvalue())
        await send_qr_code_via_email(email, qr_for_email)

    return Response(content=qr_stream.getvalue(), media_type="image/png")


@adminRouter.post("/login", response_model=schemas.Token)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db),
):
    """
    Administrator Login:
    1. Checks if the user exists in the database.
    2. Verifies the password (hash).
    3. Returns a JWT token.
    """
    admin = db.query(Admin).filter(Admin.username == form_data.username).first()

    if not admin or not security.verify_password(form_data.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = security.create_access_token(
        data={"sub": admin.username}
    )

    return {"access_token": access_token, "token_type": "bearer"}


class EmployeeResponse(BaseModel):
    uuid: uuid.UUID
    name: str
    email: str
    is_active: bool
    expires_at: Optional[datetime]  # Added to allow frontend to see the expiration date

    class Config:
        from_attributes = True


# --- UPDATED CREATE ENDPOINT ---

@adminRouter.post("/create_employee", response_model=EmployeeResponse)
async def create_employee(
    background_tasks: BackgroundTasks,
    photo: UploadFile = File(...),
    name: str = Form(...),
    email: str = Form(...),
    expiration_date: Optional[str] = Form(None), # Added optional custom expiration
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(security.get_current_active_admin)
):
    """
    Registers a new employee and triggers credentials delivery.

    Workflow:
    1. Processes the photo to generate a 512-D biometric embedding.
    2. Sets an account expiration date (defaults to 182 days if not provided).
    3. Generates a unique QR code and sends it via email as a background task.

    Args:
        photo (UploadFile): Initial biometric reference photo.
        name (str): Full name of the employee.
        email (str): Contact email for QR code delivery.
        expiration_date (datetime, optional): Specific timestamp for account expiration.
        db (Session): Database session.
        current_admin (Admin): Authenticated administrator.

    Returns:
        EmployeeResponse: The newly created employee record.
    """

    # 1. Validate if email already exists
    existing_employee = db.query(Employee).filter(Employee.email == email).first()
    if existing_employee:
        raise HTTPException(status_code=400, detail="An employee with this email already exists.")

    # 2. Process Biometrics
    photo_bytes = await photo.read()
    embedding = generate_face_embedding(photo_bytes)

    if embedding is None:
        raise HTTPException(status_code=400, detail="No face detected in the provided photo.")

    # 3. Handle Expiration Date (Logic moved here to handle string parsing safely)
    final_expiration_date = None

    if expiration_date:
        try:
            final_expiration_date = datetime.fromisoformat(expiration_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date format for expiration_date. Expected ISO string, got: {expiration_date}"
            )

    if final_expiration_date is None:
        final_expiration_date = datetime.now() + timedelta(days=182)

    # 4. Create Database Record
    new_employee = Employee(
        name=name,
        email=email,
        embedding=embedding,
        is_active=True,
        expires_at=final_expiration_date
    )

    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)

    # 5. Handle QR Code generation and dispatch
    uuid_value = str(new_employee.uuid)
    qr_stream = generate_qr_code(uuid_value)

    background_tasks.add_task(send_qr_code_via_email, email, qr_stream)

    return new_employee


# --- CRUD ENDPOINTS ---

@adminRouter.get("/employees", response_model=List[EmployeeResponse])
async def get_all_employees(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(security.get_current_active_admin)
):
    """
    Retrieves a list of all registered employees.

    Args:
        db (Session): Database session.
        current_admin (Admin): Authenticated administrator performing the request.

    Returns:
        List[schemas.Employee]: A list of employee objects including their IDs,
                                names, emails, and account status.
    """
    return db.query(Employee).all()


@adminRouter.patch("/employees/{employee_uid}/status")
async def update_employee_status(
    employee_uid: str,
    is_active: Optional[bool] = Form(None),
    expiration_date: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(security.get_current_active_admin)
):
    """
    Updates the access status and specific expiration timestamp for an employee.

    This endpoint is intended for quick administrative actions, such as
    instantly revoking access or setting a specific date/time when the
    employee's QR/access should expire.

    Args:
        employee_uid (str): The unique UUID of the employee.
        is_active (bool, optional): The new active status. If not provided,
            the current status remains unchanged.
        expiration_date (datetime, optional): A specific timestamp (ISO 8601)
            representing when the employee's access expires.
        db (Session): Database session dependency.
        current_admin (Admin): The authenticated administrator performing the action.

    Returns:
        dict: A success message along with the updated status and expiration date.

    Raises:
        HTTPException:
            - 400: If the UUID format is invalid.
            - 404: If no employee is found with the provided UUID.
    """
    try:
        uid_obj = uuid.UUID(employee_uid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    employee = db.query(Employee).filter(Employee.uuid == uid_obj).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Update activity status if provided
    if is_active is not None:
        employee.is_active = is_active

    if expiration_date is not None:
        try:
            parsed_date = datetime.fromisoformat(expiration_date.replace('Z', '+00:00'))
            employee.expires_at = parsed_date
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date format for expiration_date. Expected ISO string, got: {expiration_date}"
            )

    db.commit()
    db.refresh(employee)

    return {
        "message": "Employee status and expiration updated successfully",
        "is_active": employee.is_active,
        "expires_at": employee.expires_at
    }


@adminRouter.put("/employees/{employee_uid}")
async def update_employee(
    employee_uid: str,
    background_tasks: BackgroundTasks,
    name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    photo: UploadFile = File(None),
    is_active: Optional[bool] = Form(None),
    expiration_date: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(security.get_current_active_admin)
):
    """
    Updates an existing employee's full profile information.

    This endpoint allows for a comprehensive update, including personal details,
    biometrics (via photo upload), and administrative access controls. If a new
    photo is uploaded, the system re-calculates the facial embedding vector.

    Args:
        employee_uid (str): Unique identifier of the employee to be updated.
        name (str, optional): New full name of the employee.
        email (str, optional): New email address (must be unique across the system).
        photo (UploadFile, optional): New reference image for facial recognition.
        is_active (bool, optional): Administrative override to enable/disable access.
        expiration_date (datetime, optional): Specific timestamp for access expiration.
        db (Session): Database session dependency.
        current_admin (Admin): The authenticated administrator performing the update.

    Returns:
        dict: Confirmation message and the updated employee UUID.

    Raises:
        HTTPException:
            - 400: Invalid UUID, email already taken, or no face detected in photo.
            - 404: Employee not found.
    """
    try:
        uid_obj = uuid.UUID(employee_uid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    employee = db.query(Employee).filter(Employee.uuid == uid_obj).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    needs_new_qr = False

    if name:
        employee.name = name

    if email:
        existing = db.query(Employee).filter(Employee.email == email, Employee.uuid != uid_obj).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        employee.email = email
        needs_new_qr = True

    if is_active is not None:
        employee.is_active = is_active

    # ZMIANA: Ręczne, bezpieczne parsowanie daty ze stringa
    if expiration_date is not None:
        try:
            parsed_date = datetime.fromisoformat(expiration_date.replace('Z', '+00:00'))
            employee.expires_at = parsed_date
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date format for expiration_date. Expected ISO string, got: {expiration_date}"
            )

    if expiration_date and expiration_date.strip():
        try:
            parsed_date = datetime.fromisoformat(expiration_date.replace('Z', '+00:00'))
            employee.expires_at = parsed_date
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid date: {expiration_date}")

    if photo:
        photo_bytes = await photo.read()
        if photo_bytes:
            new_embedding = generate_face_embedding(photo_bytes)
            if new_embedding:
                employee.embedding = new_embedding
                needs_new_qr = True
    db.commit()
    db.refresh(employee)

    if needs_new_qr:
        qr_stream = generate_qr_code(str(employee.uuid))
        background_tasks.add_task(send_qr_code_via_email, employee.email, qr_stream)

    return {
        "message": "Employee updated successfully",
        "uuid": str(employee.uuid),
        "expires_at": employee.expires_at
    }


@adminRouter.delete("/employees/{employee_uid}")
async def delete_employee(employee_uid: str, db: Session = Depends(get_db), current_admin: Admin = Depends(security.get_current_active_admin)):
    """
    Permanently removes an employee and their associated data from the system.

    This action will also remove the employee's biometric embeddings and access logs.
    Revokes access immediately as the QR code associated with this ID will no longer be valid.

    Args:
        employee_id (int): The numeric ID of the employee to be deleted.
        db (Session): Database session.
        current_admin (Admin): Authenticated administrator performing the action.

    Returns:
        dict: Success message upon deletion.
    """
    try:
        uid_obj = uuid.UUID(employee_uid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    employee = db.query(Employee).filter(Employee.uuid == uid_obj).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    db.delete(employee)
    db.commit()

    return {"message": "Employee deleted successfully"}
