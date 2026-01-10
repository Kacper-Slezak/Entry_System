from fastapi import APIRouter, Response, Depends, HTTPException, status, Form, UploadFile, File
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
        login_data: schemas.AdminLogin,
        db: Session = Depends(get_db)
):
    """
    Administrator Login:
    1. Checks if the user exists in the database.
    2. Verifies the password (hash).
    3. Returns a JWT token.
    """
    admin = db.query(Admin).filter(Admin.username == login_data.username).first()

    if not admin or not security.verify_password(login_data.password, admin.hashed_password):
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
    photo: UploadFile = File(...),
    name: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Create a new employee.

    - Uploads a photo to generate a biometric embedding.
    - Saves the employee to the database.
    - Generates and sends a QR code via email.
    """
    photo_bytes = await photo.read()

    embedding = generate_face_embedding(photo_bytes)

    EmployeeRecord = Employee(
        name=name,
        email=email,
        embedding=embedding,
        is_active=True
        )
    db.add(EmployeeRecord)
    db.commit()
    db.refresh(EmployeeRecord)

    uuid_value = str(EmployeeRecord.uuid)
    qr_stream = generate_qr_code(uuid_value)

    await send_qr_code_via_email(email, qr_stream)

    return {"message": "Employee created successfully"}


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
async def get_all_employees(db: Session = Depends(get_db)):
    """
    Get a list of all employees.
    This is used to populate the main table in the Admin Panel.
    It returns employee details but excludes sensitive biometric data.
    """
    employees = db.query(Employee).all()
    return employees


@adminRouter.patch("/employees/{employee_uid}/toggle-access")
async def toggle_employee_access(employee_uid: str, db: Session = Depends(get_db)):
    """
    Enable or disable access for a specific employee.
    If set to False (Blocked), the employee cannot enter using QR or FaceID.
    """
    try:
        uid_obj = uuid.UUID(employee_uid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    employee = db.query(Employee).filter(Employee.uuid == uid_obj).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Toggle the boolean status
    employee.is_active = not employee.is_active
    db.commit()
    db.refresh(employee)

    status_msg = "Active" if employee.is_active else "Blocked"
    return {"message": f"Employee status changed to: {status_msg}", "is_active": employee.is_active}


@adminRouter.put("/employees/{employee_uid}")
async def update_employee(
    employee_uid: str,
    name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    photo: UploadFile = File(None),  # Optional new photo
    db: Session = Depends(get_db)
):
    """
    Update employee details (Name, Email, Photo).
    If a new photo is uploaded, the system will automatically re-calculate
    the biometric embedding.
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
async def delete_employee(employee_uid: str, db: Session = Depends(get_db)):
    """
    Permanently remove an employee and their biometric data from the database.
    This action cannot be undone.
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
