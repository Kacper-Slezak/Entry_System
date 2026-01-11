import io

from fastapi import APIRouter, Response, Depends, HTTPException, status, Form, UploadFile, File
from sqlalchemy.orm import Session
from app.utils import generate_qr_code, send_qr_code_via_email
from app.services.biometric_service import generate_face_embedding
from app.db.models import Employee, Admin, AccessLog
from app.db.session import get_db
from io import BytesIO

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
    On address /admin/qr_test/{uuid_value} you will get a QR code image
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
    Administartor Login:
    1. Checks if the user exitsts in the database.
    2. Verifies the password (hash).
    3. Returns a JWT token.
    """

    admin = db.query(models.Admin).filter(models.Admin.username == login_data.username).first()

    if not admin or not security.verify_password(login_data.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy login lub hasło",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = security.create_access_token(
        data={"sub": admin.username}
    )

    return {"access_token": access_token, "token_type": "bearer"}

@adminRouter.post("/create_employee")
async def create_employee(photo: UploadFile = File(...), name: str = Form(...), email: str = Form(...), db: Session = Depends(get_db)):
    """
    Endpoint to create a new employee.
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