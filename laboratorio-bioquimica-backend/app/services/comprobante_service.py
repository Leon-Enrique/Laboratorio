"""Generación de comprobantes / facturas de orden — formato A4 Genotipia."""
from __future__ import annotations

import io
import os
from datetime import datetime
from typing import List, Optional, Tuple
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app.models.orden import Orden
from app.services import qr_service

TZ_LAB = "America/La_Paz"
MESES_ES = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)

C_GREEN = colors.HexColor("#059669")
C_BLUE = colors.HexColor("#1e40af")
C_SLATE = colors.HexColor("#334155")
C_MUTED = colors.HexColor("#64748b")
C_BORDER = colors.HexColor("#94a3b8")
C_ORANGE = colors.HexColor("#ea580c")
C_BG_HEAD = colors.HexColor("#d1d5db")
C_BG_TOTAL = colors.HexColor("#e5e7eb")

LAB_DIRECCION = (
    "Dirección Av. Japón #3555, 3er anillo externo Telf.: 75548529 "
    "(Diagonal entrada emerg. Hosp. Japonés)"
)

PAGE_W, PAGE_H = A4
MARGIN_X = 1.25 * cm
MARGIN_TOP = 1.0 * cm
CONTENT_W = PAGE_W - 2 * MARGIN_X


def _get_tz():
    try:
        return ZoneInfo(TZ_LAB)
    except ZoneInfoNotFoundError:
        from datetime import timezone, timedelta
        return timezone(timedelta(hours=-4))


def _to_local(dt: Optional[datetime]) -> datetime:
    if dt is None:
        return datetime.now(_get_tz())
    if dt.tzinfo is None:
        return dt.replace(tzinfo=_get_tz())
    return dt.astimezone(_get_tz())


def _fmt_fecha_larga(dt: Optional[datetime]) -> str:
    local = _to_local(dt)
    return f"{local.day} de {MESES_ES[local.month - 1]} del {local.year}"


def _fmt_fecha_hora(dt: Optional[datetime]) -> str:
    return _to_local(dt).strftime("%d/%m/%Y %H:%M:%S")


def _fmt_bs(valor: float) -> str:
    return f"{valor:.2f}".replace(".", ",")


def _edad_texto(fecha_nac, ref=None) -> str:
    from datetime import date
    ref = ref or _to_local(None).date()
    anos = ref.year - fecha_nac.year
    meses = ref.month - fecha_nac.month
    if ref.day < fecha_nac.day:
        meses -= 1
    if meses < 0:
        anos -= 1
        meses += 12
    return f"{anos} AÑOS {meses} MESES"


def _logo_path() -> Optional[str]:
    root = os.path.dirname(os.path.dirname(__file__))
    repo_root = os.path.dirname(os.path.dirname(root))
    candidates = [
        os.path.join(root, "assets", "logo-genotipia.png"),
        os.path.join(root, "assets", "logo-genotipia-full.png"),
        os.path.join(repo_root, "laboratorio-bioquimica-web", "public", "branding", "logo-genotipia-full.png"),
        os.path.join(repo_root, "laboratorio-bioquimica-web", "public", "branding", "logo-genotipia.png"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def _invoices_dir() -> str:
    base = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage", "invoices"
    )
    os.makedirs(base, exist_ok=True)
    return base


def ruta_comprobante(codigo_orden: str) -> str:
    return os.path.join(_invoices_dir(), f"{codigo_orden}.pdf")


def comprobante_existe(codigo_orden: str) -> bool:
    return os.path.isfile(ruta_comprobante(codigo_orden.strip().upper()))


def invalidar_comprobante(codigo_orden: str) -> None:
    path = ruta_comprobante(codigo_orden.strip().upper())
    if os.path.isfile(path):
        os.remove(path)


def _label_metodo(metodo: Optional[str]) -> str:
    labels = {
        "EFECTIVO": "Contado",
        "TRANSFERENCIA": "Transferencia",
        "TARJETA": "Tarjeta",
        "QR": "QR",
    }
    return labels.get((metodo or "").upper(), "Contado")


def _wrap_lines(c: canvas.Canvas, text: str, font: str, size: float, max_w: float) -> List[str]:
    words = text.split()
    if not words:
        return [""]
    lines: List[str] = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if c.stringWidth(trial, font, size) <= max_w:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _draw_label_value_grid(
    c: canvas.Canvas,
    x: float,
    y_top: float,
    w: float,
    rows: List[Tuple[str, str, str, str]],
    row_h: float = 8 * mm,
) -> float:
    """Cuadro paciente estilo ClinicFast: 4 columnas por fila."""
    pad = 2.5 * mm
    col_w = (w - 2 * pad) / 4
    box_h = row_h * len(rows) + 2 * pad
    y_bottom = y_top - box_h

    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.roundRect(x, y_bottom, w, box_h, 6, stroke=1, fill=0)

    y = y_top - pad - 7
    lbl_size = 7.5
    val_size = 9
    for lbl1, val1, lbl2, val2 in rows:
        c.setFont("Helvetica-Bold", lbl_size)
        c.setFillColor(C_BLUE)
        c.drawString(x + pad, y, lbl1)
        c.drawString(x + pad + col_w * 2, y, lbl2)

        c.setFont("Helvetica-Bold", val_size)
        c.setFillColor(C_SLATE)
        c.drawString(x + pad + col_w, y, val1[:42])
        c.drawString(x + pad + col_w * 3, y, val2[:28])
        y -= row_h

    return y_bottom - 3 * mm


def _draw_sello_pagado(
    c: canvas.Canvas,
    x: float,
    w: float,
    y_first_box: float,
    y_last_box: float,
    foot_h: float,
    y_table_bottom: float,
    sep: float,
) -> None:
    """Marca PAGADO a la izquierda, solo en la franja de totales (sin tapar la tabla)."""
    stamp_size = 28
    font = "Helvetica-Bold"
    text = "PAGADO"

    block_top = y_first_box + foot_h
    block_bottom = y_last_box
    stamp_baseline = (block_top + block_bottom) / 2 - 1.5 * mm

    # No invadir la tabla: el texto no puede subir del borde inferior + separación
    max_top = y_table_bottom - sep - 1 * mm
    stamp_baseline = min(stamp_baseline, max_top - stamp_size * 0.72)
    stamp_baseline = max(stamp_baseline, block_bottom + 2 * mm)

    stamp_w = c.stringWidth(text, font, stamp_size)
    max_right = x + w * 0.36
    stamp_x = x + 3 * mm
    if stamp_x + stamp_w > max_right:
        stamp_size = 22
        stamp_w = c.stringWidth(text, font, stamp_size)

    c.saveState()
    c.setFillAlpha(0.45)
    c.setFillColor(colors.HexColor("#ef4444"))
    c.setFont(font, stamp_size)
    c.drawString(stamp_x, stamp_baseline, text)
    c.restoreState()


def _draw_bloque_totales(
    c: canvas.Canvas,
    x: float,
    y_table_bottom: float,
    w: float,
    total: float,
    pagado: float,
    saldo: float,
    sello_pagado: bool = False,
) -> float:
    """Total / Pagado / Saldo debajo de la tabla, montos en cajita a la derecha."""
    foot_h = 7.5 * mm
    gap = 2 * mm
    sep = 4 * mm
    pad_x = 3 * mm
    text_off = 2.2 * mm
    right = x + w
    font = "Helvetica-Bold"
    size = 10

    filas = [
        ("Total a Pagar (Bs.):", total, True),
        ("Pagado:", pagado, False),
        ("Saldo:", saldo, False),
    ]

    valores = [_fmt_bs(v) for _, v, _ in filas]
    box_w = max(max(c.stringWidth(v, font, size) for v in valores) + 2 * pad_x, 22 * mm)
    box_x = right - box_w
    y_first_box = y_table_bottom - sep - foot_h
    y_last_box = y_first_box - (len(filas) - 1) * (foot_h + gap)
    y_box = y_first_box

    if sello_pagado:
        _draw_sello_pagado(c, x, w, y_first_box, y_last_box, foot_h, y_table_bottom, sep)

    for label, valor, con_fondo in filas:
        val_txt = _fmt_bs(valor)
        label_right = box_x - 2 * mm
        label_left = label_right - c.stringWidth(label, font, size)
        text_y = y_box + text_off

        if con_fondo:
            c.setFillColor(C_BG_TOTAL)
            c.rect(label_left - 2 * mm, y_box, right - label_left + 2 * mm, foot_h, fill=1, stroke=0)

        c.setFillColor(C_SLATE)
        c.setFont(font, size)
        c.drawRightString(label_right, text_y, label)

        c.setStrokeColor(colors.black)
        c.setLineWidth(0.7)
        c.setFillColor(colors.white)
        c.rect(box_x, y_box, box_w, foot_h, stroke=1, fill=1)

        c.setFillColor(C_SLATE)
        c.setFont(font, size)
        c.drawCentredString(box_x + box_w / 2, text_y, val_txt)

        y_box -= foot_h + gap

    return y_box - 2 * mm


def _draw_items_table(
    c: canvas.Canvas,
    x: float,
    y_top: float,
    w: float,
    items: List[Tuple[str, float]],
    total: float,
    pagado: float,
    saldo: float,
    sello_pagado: bool = False,
) -> float:
    col_w = [w * 0.52, w * 0.16, w * 0.14, w * 0.18]
    row_h = 8 * mm
    head_h = 9 * mm
    body_rows = max(len(items), 1)
    table_h = head_h + body_rows * row_h

    y_bottom = y_top - table_h

    c.setStrokeColor(colors.black)
    c.setLineWidth(0.8)
    c.rect(x, y_bottom, w, table_h, stroke=1, fill=0)

    # Encabezado gris
    c.setFillColor(C_BG_HEAD)
    c.rect(x, y_top - head_h, w, head_h, stroke=0, fill=1)
    c.setFillColor(C_SLATE)
    c.setFont("Helvetica-Bold", 9)
    headers = ["Detalle de la Orden, Laboratorio", "Precio", "Cant.", "Subtotal"]
    aligns = ["left", "right", "right", "right"]
    cx = x
    for i, (hdr, cw, align) in enumerate(zip(headers, col_w, aligns)):
        tx = cx + 4 if align == "left" else cx + cw - 4
        if align == "right":
            c.drawRightString(tx, y_top - head_h + 3 * mm, hdr)
        else:
            c.drawString(tx, y_top - head_h + 3 * mm, hdr)
        if i < 3:
            c.line(cx + cw, y_bottom, cx + cw, y_top)
        cx += cw

    c.line(x, y_top - head_h, x + w, y_top - head_h)

    # Ítems
    y = y_top - head_h - row_h + 3 * mm
    c.setFont("Helvetica", 10)
    c.setFillColor(C_SLATE)
    if items:
        for idx, (nombre, precio) in enumerate(items):
            lines = _wrap_lines(c, nombre.upper(), "Helvetica", 10, col_w[0] - 8)
            c.drawString(x + 4, y, lines[0][:80])
            c.drawRightString(x + col_w[0] + col_w[1] - 4, y, _fmt_bs(precio))
            c.drawRightString(x + col_w[0] + col_w[1] + col_w[2] - 4, y, "1,00")
            c.drawRightString(x + w - 4, y, _fmt_bs(precio))
            y -= row_h
            if idx < len(items) - 1:
                c.line(x, y + row_h - 3 * mm, x + w, y + row_h - 3 * mm)
    else:
        c.drawString(x + 4, y, "SIN ÍTEMS")
        y -= row_h

    # Totales debajo de la tabla, alineados a la derecha (como referencia)
    return _draw_bloque_totales(
        c, x, y_bottom, w, total, pagado, saldo, sello_pagado=sello_pagado
    )


def generar_comprobante_orden(orden: Orden, usuario_nombre: str) -> str:
    """Genera PDF A4 completo al estilo comprobante de laboratorio."""
    path = ruta_comprobante(orden.codigo_orden)
    numero = orden.numero_comprobante or orden.id
    paciente = orden.paciente
    medico = (orden.medico_solicitante or "PARTICULAR").upper()
    centro = "PARTICULAR"
    matricula = str(paciente.id).zfill(5)
    total = float(orden.precio_total or 0)
    pagado = total if (orden.estado_pago or "") == "PAGADO" else 0.0
    saldo = max(total - pagado, 0.0)
    fecha_doc = orden.fecha_pago or orden.fecha_creacion
    recepcionista = usuario_nombre
    if orden.recepcionista and orden.recepcionista.nombre:
        recepcionista = orden.recepcionista.nombre

    titulo_doc = "FACTURA" if orden.requiere_factura else "ORDEN"
    items: List[Tuple[str, float]] = []
    for res in orden.resultados:
        if res.examen:
            items.append((res.examen.nombre, float(res.examen.precio_bob or 0)))

    c = canvas.Canvas(path, pagesize=A4)
    c.setTitle(f"{titulo_doc} {numero}")
    x = MARGIN_X
    y = PAGE_H - MARGIN_TOP

    # Logo + título
    logo = _logo_path()
    logo_h = 3.2 * cm
    if logo:
        c.drawImage(ImageReader(logo), x, y - logo_h, width=7.2 * cm, height=logo_h, preserveAspectRatio=True, mask="auto")
    else:
        c.setFont("Helvetica-Bold", 22)
        c.setFillColor(C_GREEN)
        c.drawString(x, y - 12 * mm, "GENOTIPIA")
        c.setFillColor(C_BLUE)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(x, y - 22 * mm, "LABORATORIO CLÍNICO")

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 24)
    c.drawRightString(x + CONTENT_W, y - 10 * mm, f"{titulo_doc} Nº {numero}")
    c.setFont("Helvetica", 11)
    c.drawRightString(x + CONTENT_W, y - 20 * mm, f"Fecha, {_fmt_fecha_larga(fecha_doc)}")

    y -= logo_h + 4 * mm
    c.setFont("Helvetica", 9)
    c.setFillColor(C_MUTED)
    c.drawString(x, y, LAB_DIRECCION)
    y -= 10 * mm

    pac_rows = [
        ("PACIENTE:", f"{paciente.apellido} {paciente.nombre}".upper(), "EDAD:", _edad_texto(paciente.fecha_nacimiento)),
        ("DOCTOR:", medico, "MAT.:", matricula),
        ("CENTRO:", centro, "TELF.:", paciente.telefono or "—"),
    ]
    if orden.requiere_factura and orden.nit_factura:
        pac_rows.append(
            ("NIT:", orden.nit_factura, "RAZÓN SOC.:", (orden.razon_social_factura or "—").upper()[:28])
        )

    y = _draw_label_value_grid(c, x, y, CONTENT_W, pac_rows, row_h=8 * mm)
    y = _draw_items_table(
        c, x, y, CONTENT_W, items, total, pagado, saldo,
        sello_pagado=(orden.estado_pago == "PAGADO"),
    )

    if orden.estado_pago == "PAGADO":
        c.setFillColor(C_SLATE)
        c.setFont("Helvetica", 11)
        pago_txt = (
            f"Pago # {orden.id}, {_fmt_fecha_hora(orden.fecha_pago)}, "
            f"Importe {_fmt_bs(total)} {_label_metodo(orden.metodo_pago)}"
        )
        c.drawCentredString(x + CONTENT_W / 2, y - 4 * mm, pago_txt)
        y -= 12 * mm
    else:
        c.setFillColor(C_MUTED)
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(x + CONTENT_W / 2, y - 4 * mm, "PENDIENTE DE PAGO")
        y -= 14 * mm

    url_resultados = qr_service.url_resultados_orden(orden.codigo_orden)
    c.setFont("Helvetica", 8.5)
    c.setFillColor(C_BLUE)
    url_txt = f"Resultado en línea {url_resultados}"
    if c.stringWidth(url_txt, "Helvetica", 8.5) > CONTENT_W - 4 * mm:
        c.drawCentredString(x + CONTENT_W / 2, y, "Resultado en línea")
        y -= 4 * mm
        c.drawCentredString(x + CONTENT_W / 2, y, url_resultados)
    else:
        c.drawCentredString(x + CONTENT_W / 2, y, url_txt)
    y -= 10 * mm

    # Pie + QR anclados abajo (llenan la hoja A4)
    qr_size = 5.5 * cm
    footer_y = 2.2 * cm
    qr_bottom = footer_y + 14 * mm

    c.setStrokeColor(C_BORDER)
    c.setLineWidth(0.5)
    c.line(x, qr_bottom + qr_size + 8 * mm, x + CONTENT_W, qr_bottom + qr_size + 8 * mm)

    c.setFont("Helvetica", 9)
    c.setFillColor(C_MUTED)
    c.drawString(x, footer_y + 6 * mm, f"Fecha: {_fmt_fecha_hora(datetime.now(_get_tz()))}")
    c.drawRightString(x + CONTENT_W, footer_y + 6 * mm, f"Usuario: {recepcionista[:40]}")

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(x + CONTENT_W / 2, qr_bottom + qr_size + 4 * mm, "VER RESULTADO")

    qr_bytes = qr_service.generar_qr_png(url_resultados)
    c.drawImage(
        ImageReader(io.BytesIO(qr_bytes)),
        x + (CONTENT_W - qr_size) / 2,
        qr_bottom,
        width=qr_size,
        height=qr_size,
    )

    c.save()
    return path
