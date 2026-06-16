"""Generación de códigos QR para órdenes."""
import io

import qrcode
from qrcode.constants import ERROR_CORRECT_M


def generar_qr_png(url: str) -> bytes:
    qr = qrcode.QRCode(version=1, error_correction=ERROR_CORRECT_M, box_size=8, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1e3a8a", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
