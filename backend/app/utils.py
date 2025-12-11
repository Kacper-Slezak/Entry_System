from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from fastapi import UploadFile
import qrcode
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer
from io import BytesIO
import os
from dotenv import load_dotenv

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
    Docstring for send_qr_code_via_email
    
    :param email: Description
    :type email: str
    :param qr_code_stream: Description
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
