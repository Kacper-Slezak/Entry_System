import qrcode
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer
from io import BytesIO

def generate_qr_code(data: str) -> BytesIO:
    """Generate a QR code image in PNG format from the given data string.

    Args:
        data (str): The data to encode in the QR code - UUID

    Returns:
        bytes: The PNG image data of the generated QR code.
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