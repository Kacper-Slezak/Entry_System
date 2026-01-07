from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from fastapi import UploadFile
import qrcode
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer
from io import BytesIO
import os
from dotenv import load_dotenv
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.db import models

load_dotenv()

def generate_qr_code(data: str) -> BytesIO:
    """Generate a QR code image in PNG format from the given data string.

    Args:
        data (str): The data to encode in the QR code - UUID

    Returns:
        BytesIO: A BytesIO stream containing the PNG image of the QR code.
    """
    qr=qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white", module_drawer=RoundedModuleDrawer())

    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    return img_byte_arr

conf = ConnectionConfig(
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", ""),
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", ""),
    MAIL_FROM = os.getenv("MAIL_FROM"),
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_STARTTLS = os.getenv("MAIL_STARTTLS", "True"),
    MAIL_SSL_TLS = os.getenv("MAIL_SSL_TLS", "False"),
    USE_CREDENTIALS = os.getenv("USE_CREDENTIALS", "True"),
    VALIDATE_CERTS = os.getenv("VALIDATE_CERTS", "True")
)

async def send_qr_code_via_email(email: str, qr_code_stream: BytesIO):
    """
    Sending an email with the QR code as an attachment.

    Function packeges the Qr BytesIO stream into an UploadFile object and sends it as an email attachment.

    Args:
    :param email: Recipient email address
    :type email: str
    :param qr_code_stream: BytesIO stream containing the QR code image
    :type qr_code_stream: BytesIO
    """
    qr_code_file = UploadFile(file=qr_code_stream, filename="qrcode.png")
    message = MessageSchema(
        subject="Witamy w firmie! Oto Twój kod QR",
        recipients=[email],
        body="W załączniku znajduje się Twój kod QR.",
        subtype="html",
        attachments=[qr_code_file]
    )
    fm = FastMail(conf)
    await fm.send_message(message)

def create_default_admin():
    """
    Checking if the admin is created in data base.
    If not, it creates a new default admin account 'admin' with password 'admin123'.
    """
    db = SessionLocal()
    try:
        admin = db.query(models.Admin).first()
        if not admin:
            print("INFO: Tworzenie domyślnego konta administratora...")
            default_admin = models.Admin(
                username = "admin",
                hashed_password = get_password_hash("admin123")
            )
            db.add(default_admin)
            db.commit()
            print("INFO: Utworzono konto administratora: admin / admin123")
    finally:
        db.close()
