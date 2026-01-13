import io

from datetime import datetime, timedelta
from fastapi import APIRouter, Response, Depends, HTTPException, status, Form, UploadFile, File, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.utils import generate_qr_code, send_qr_code_via_email
from app.services.biometric_service import generate_face_embedding
from app.db.models import Employee, Admin, AccessLog
from app.db.session import get_db
from io import BytesIO
from typing import List, Optional
from pydantic import BaseModel
import uuid

from app.core import security
from app import schemas
from app.schemas import AccessLogReport
from typing import List, Optional
from datetime import datetime, time, date
import csv
from fastapi.responses import StreamingResponse


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


@adminRouter.post("/create_employee")
async def create_employee(
    background_tasks: BackgroundTasks,
    photo: UploadFile = File(...),
    name: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(security.get_current_active_admin)
):
    """
    Registers a new employee in the system and triggers credentials delivery.

    The process includes:
    1. Processing the photo to generate a 512-D biometric embedding.
    2. Setting an default account expiration date (182 days).
    3. Generating a unique QR code and sending it via email as a background task.

    Args:
        photo (UploadFile): Initial biometric reference photo.
        name (str): Full name of the employee.
        email (str): Contact email for QR code delivery.
        db (Session): Database session.
        current_admin (Admin): Authenticated administrator performing the action.

    Returns:
        dict: Confirmation message on successful creation.
    """
    photo_bytes = await photo.read()

    expiration_date = datetime.now() + timedelta(days=182)

    embedding = generate_face_embedding(photo_bytes)

    EmployeeRecord = Employee(
        name=name,
        email=email,
        embedding=embedding,
        is_active=True,
        expires_at=expiration_date
        )
    db.add(EmployeeRecord)
    db.commit()
    db.refresh(EmployeeRecord)

    uuid_value = str(EmployeeRecord.uuid)
    qr_stream = generate_qr_code(uuid_value)

    background_tasks.add_task(send_qr_code_via_email, email, qr_stream)

    return {"message": "Employee created successfully"}


@adminRouter.get("/logs", response_model=List[AccessLogReport])
def get_logs(
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[str] = None,
        db: Session = Depends(get_db)
):
    """
    Downloads entry history. It can be filtered by a date or status.
    """
    query = db.query(AccessLog).order_by(AccessLog.timestamp.desc())

    if start_date:
        query = query.filter(AccessLog.timestamp >= datetime.combine(start_date, time.min))
    if end_date:
        query = query.filter(AccessLog.timestamp <= datetime.combine(end_date, time.max))

    # Filtering by status
    if status:
        query = query.filter(AccessLog.status == status)

    logs = query.all()

    # Data mapping
    results = []
    for log in logs:
        emp_name = log.employee.name if log.employee else "Unknown / Wrong QR code"
        emp_email = log.employee.email if log.employee else "-"

        results.append(AccessLogReport(
            id=log.id,
            timestamp=log.timestamp,
            status=log.status,
            reason=log.reason,
            employee_name=emp_name,
            employee_email=emp_email
        ))

    return results


@adminRouter.get("/logs/export")
def export_logs_csv(db: Session = Depends(get_db)):
    """
    Generates a .csv file with full history, which can be opened in Excel.
    """
    logs = db.query(AccessLog).order_by(AccessLog.timestamp.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')

    writer.writerow(["ID", "Date", "Hour", "Status", "Reason", "Worker Name", "Email"])

    for log in logs:
        emp_name = log.employee.name if log.employee else "Unknown"
        emp_email = log.employee.email if log.employee else "-"

        writer.writerow([
            log.id,
            log.timestamp.strftime("%Y-%m-%d"),
            log.timestamp.strftime("%H:%M:%S"),
            log.status.value,
            log.reason,
            emp_name,
            emp_email
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=raport_wejsc.csv"}
    )
# --- RESPONSE MODELS ---

class EmployeeResponse(BaseModel):
    uuid: uuid.UUID
    name: str
    email: str
    is_active: bool
    # We deliberately skip 'embedding' here to keep the response clean

    class Config:
        from_attributes = True


# --- CRUD ENDPOINTS ---

@adminRouter.get("/employees", response_model=List[EmployeeResponse])
async def get_all_employees(db: Session = Depends(get_db), current_admin: Admin = Depends(security.get_current_active_admin)):
    """
    Retrieves a list of all registered employees.

    Args:
        db (Session): Database session.
        current_admin (Admin): Authenticated administrator performing the request.

    Returns:
        List[schemas.Employee]: A list of employee objects including their IDs,
                                names, emails, and account status.
    """

    employees = db.query(Employee).all()
    return employees


@adminRouter.patch("/employees/{employee_uid}/status")
async def update_employee_status(
    employee_uid: str,
    is_active: Optional[bool] = Form(None),
    expiration_days: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(security.get_current_active_admin)
):
    """
    Updates the access status and expiration period for a specific employee.

    This endpoint allows administrators to manually enable/disable access or
    extend the QR code validity by a specific number of days.

    Args:
        employee_uid (str): Unique identifier (UUID) of the employee.
        is_active (bool, optional): New activity status. If None, remains unchanged.
        expiration_days (int, optional): Number of days from now to set as the new
                                         expiration date.
        db (Session): Database session.
        current_admin (Admin): Authenticated administrator.

    Returns:
        dict: Updated employee status and the new expiration timestamp.

    Raises:
        HTTPException: 404 if the employee is not found.
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

    # Update expiration date if days are provided
    if expiration_days is not None:
        employee.expires_at = datetime.now() + timedelta(days=expiration_days)

    db.commit()
    db.refresh(employee)

    return {
        "message": "Employee status updated",
        "is_active": employee.is_active,
        "expires_at": employee.expires_at
    }


@adminRouter.put("/employees/{employee_uid}")
async def update_employee(
    employee_uid: str,
    name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    photo: UploadFile = File(None),  # Optional new photo
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(security.get_current_active_admin)
):
    """
    Updates an existing employee's profile information.

    If a new photo is provided, the system automatically re-triggers the biometric
    service to generate and update the facial embedding vector.

    Args:
        employee_uid (str): Unique identifier of the employee.
        name (str, optional): New name to be assigned.
        email (str, optional): New email address (must be unique).
        photo (UploadFile, optional): New reference photo for biometric updates.
        db (Session): Database session.
        current_admin (Admin): Authenticated administrator.

    Raises:
        HTTPException: 404 if employee not found, 400 if email is already in use
                       or no face is detected in the new photo.
    """
    try:
        uid_obj = uuid.UUID(employee_uid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    employee = db.query(Employee).filter(Employee.uuid == uid_obj).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # 1. Update basic info if provided
    if name:
        employee.name = name
    if email:
        # Check for unique email constraint (excluding current user)
        existing = db.query(Employee).filter(Employee.email == email, Employee.uuid != uid_obj).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        employee.email = email

    # 2. Update photo and biometrics if provided
    if photo:
        photo_bytes = await photo.read()
        if photo_bytes:
            # Generate new embedding using the biometric service
            new_embedding = generate_face_embedding(photo_bytes)

            if new_embedding is None:
                raise HTTPException(status_code=400, detail="No face detected in the new photo. Update failed.")

            employee.embedding = new_embedding

    db.commit()
    db.refresh(employee)

    return {"message": "Employee updated successfully", "uuid": str(employee.uuid)}


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
