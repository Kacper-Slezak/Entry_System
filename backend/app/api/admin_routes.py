from fastapi import APIRouter, Response
from backend.app.utils import generate_qr_code

adminRouter = APIRouter(prefix="/admin", tags=["admin"])

@adminRouter.get("/health")
async def health_check():
    return {200: "OK"}

@adminRouter.get("/qr_test/{uuid_value}")
async def qr_test(uuid_value: str):
    """
    Generates a QR code for the given UUID value.
    On address /admin/qr_test/{uuid_value} you will get a QR code image
    """
    qr_stream = generate_qr_code(text)
    

    return Response(content=qr_stream.getvalue(), media_type="image/png")