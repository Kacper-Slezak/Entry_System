from fastapi import APIRouter, Response, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.utils import generate_qr_code
from app.utils import send_qr_code_via_email
from io import BytesIO

# Nie umiem inaczej :'(
from backend.app.core import security
from backend.app import schemas
from backend.app.db import models
from backend.app.db.session import get_db


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
