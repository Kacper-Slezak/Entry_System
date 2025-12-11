from fastapi import APIRouter, Response, Form, UploadFile, File, Depends
from app.utils import generate_qr_code, send_qr_code_via_email
from app.services.biometric_service import generate_face_embedding
from sqlalchemy.orm import Session
from app.db.models import Employee
from app.db.session import get_db
from io import BytesIO


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
