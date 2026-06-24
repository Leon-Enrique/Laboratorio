"""Generación de códigos QR para órdenes."""
import io

import qrcode
from qrcode.constants import ERROR_CORRECT_M

from app.core.config import settings


def url_resultados_orden(codigo_orden: str) -> str:
    codigo = codigo_orden.strip().upper()
    base = settings.public_site_url
    return f"{base}/resultados?codigo={codigo}"


def generar_qr_png(url: str) -> bytes:
    qr = qrcode.QRCode(version=1, error_correction=ERROR_CORRECT_M, box_size=8, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#000000", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
