"""Generación de informes PDF clínicos — formato profesional Genotipia."""
from __future__ import annotations

import io
import os
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models.orden import Orden
from app.services import qr_service

TZ_LAB = "America/La_Paz"

# Marca Genotipia
C_GREEN = colors.HexColor("#059669")
C_GREEN_LIGHT = colors.HexColor("#10b981")
C_TEAL = colors.HexColor("#0d9488")
C_BLUE = colors.HexColor("#1e40af")
C_BLUE_DARK = colors.HexColor("#1e3a8a")
C_SLATE = colors.HexColor("#334155")
C_MUTED = colors.HexColor("#64748b")
C_BORDER = colors.HexColor("#cbd5e1")
C_BG_SOFT = colors.HexColor("#f0fdf4")
C_BG_HEADER = colors.HexColor("#ecfdf5")
C_YELLOW = colors.HexColor("#fbbf24")
C_WHITE = colors.white

LAB_TELEFONO = "75548529"
LAB_EMAIL = "genotipia2024@gmail.com"
LAB_WEB = "www.genotipia-lab.com"
LAB_DIRECCION = (
    "Av. Japón #3555, 3er anillo externo — Diagonal entrada emergencias Hospital Japonés"
)
LAB_CIUDAD = "SANTA CRUZ DE LA SIERRA — BOLIVIA"
LAB_TAGLINE = "Precisión y cuidado en cada análisis"


def _get_tz():
    try:
        return ZoneInfo(TZ_LAB)
    except ZoneInfoNotFoundError:
        from datetime import timezone, timedelta

        return timezone(timedelta(hours=-4))


def _reports_dir() -> str:
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage", "reports")
    os.makedirs(base, exist_ok=True)
    return base


def ruta_informe(codigo_orden: str) -> str:
    return os.path.join(_reports_dir(), f"{codigo_orden}.pdf")


def informe_existe(codigo_orden: str) -> bool:
    return os.path.isfile(ruta_informe(codigo_orden))


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


def _to_local(dt: Optional[datetime]) -> datetime:
    if dt is None:
        return datetime.now(_get_tz())
    if dt.tzinfo is None:
        return dt.replace(tzinfo=_get_tz())
    return dt.astimezone(_get_tz())


def _fmt_fecha_hora(dt: Optional[datetime]) -> str:
    return _to_local(dt).strftime("%d/%m/%Y %H:%M:%S")


def _edad_texto(fecha_nac: date, ref: Optional[date] = None) -> str:
    ref = ref or _to_local(None).date()
    anos = ref.year - fecha_nac.year
    meses = ref.month - fecha_nac.month
    if ref.day < fecha_nac.day:
        meses -= 1
    if meses < 0:
        anos -= 1
        meses += 12
    return f"{anos} años {meses} meses"


def _parametro_clave(nombre: str, unidad: Optional[str]) -> str:
    return f"{nombre} ({unidad})" if unidad else nombre


def _obtener_valor(valores: dict, nombre: str, unidad: Optional[str]) -> str:
    if not valores:
        return "—"
    claves = [_parametro_clave(nombre, unidad), nombre]
    for k in claves:
        if k in valores and valores[k] is not None and str(valores[k]).strip() != "":
            return str(valores[k]).strip()
    nombre_lower = nombre.lower()
    for k, v in valores.items():
        if v is not None and str(v).strip() and nombre_lower in k.lower():
            return str(v).strip()
    return "—"


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )


def _referencia_texto(
    valor_min: Optional[float],
    valor_max: Optional[float],
    valor_ref: Optional[str],
    unidad: Optional[str],
) -> str:
    if valor_ref and str(valor_ref).strip():
        return str(valor_ref).strip()
    suf = f" {unidad}" if unidad else ""
    if valor_min is not None and valor_max is not None:
        return f"{valor_min:g} – {valor_max:g}{suf}"
    if valor_max is not None:
        return f"≤ {valor_max:g}{suf}"
    if valor_min is not None:
        return f"≥ {valor_min:g}{suf}"
    return ""


def _es_numerico(valor: str) -> bool:
    try:
        float(str(valor).replace(",", ".").strip())
        return True
    except (TypeError, ValueError):
        return False


def _evaluar_flag(valor_str: str, vmin: Optional[float], vmax: Optional[float]) -> Tuple[str, colors.Color]:
    try:
        valor = float(str(valor_str).replace(",", ".").strip())
    except (TypeError, ValueError):
        return "—", C_MUTED
    if vmin is not None and valor < vmin:
        return "Bajo", colors.HexColor("#d97706")
    if vmax is not None and valor > vmax:
        return "Alto", colors.HexColor("#dc2626")
    return "Normal", C_GREEN


class _FilaResultado:
    __slots__ = ("etiqueta", "valor", "ref", "unidad", "tipo", "vmin", "vmax", "es_tabla")

    def __init__(
        self,
        etiqueta: str,
        valor: str,
        ref: Optional[str] = None,
        unidad: Optional[str] = None,
        tipo: Optional[str] = None,
        vmin: Optional[float] = None,
        vmax: Optional[float] = None,
    ):
        self.etiqueta = etiqueta
        self.valor = valor
        self.ref = ref
        self.unidad = unidad or ""
        self.tipo = (tipo or "").strip()
        self.vmin = vmin
        self.vmax = vmax
        t = self.tipo.lower()
        largo = len(valor) > 100 or "\n" in valor
        es_num = t == "numero" or (_es_numerico(valor) and not largo and (vmin is not None or vmax is not None or ref))
        self.es_tabla = es_num and not largo and t not in ("texto area", "texto")


def _filas_resultado_examen(res) -> List[_FilaResultado]:
    examen = res.examen
    if not examen:
        return []
    valores = res.valor_resultado or {}
    filas: List[_FilaResultado] = []
    claves_usadas = set()
    parametros = sorted(examen.parametros, key=lambda p: p.orden) if examen.parametros else []

    if parametros:
        for p in parametros:
            clave = _parametro_clave(p.nombre, p.unidad)
            val = _obtener_valor(valores, p.nombre, p.unidad)
            claves_usadas.add(clave)
            claves_usadas.add(p.nombre)
            ref = _referencia_texto(p.valor_min, p.valor_max, p.valor_referencia, p.unidad) or None
            filas.append(
                _FilaResultado(
                    etiqueta=p.nombre.upper(),
                    valor=val,
                    ref=ref,
                    unidad=p.unidad,
                    tipo=p.tipo,
                    vmin=p.valor_min,
                    vmax=p.valor_max,
                )
            )
        for k, v in valores.items():
            if k in claves_usadas or v is None or str(v).strip() == "":
                continue
            filas.append(_FilaResultado(etiqueta=k.upper(), valor=str(v).strip()))
    elif valores:
        for k, v in valores.items():
            if v is None or str(v).strip() == "":
                continue
            filas.append(_FilaResultado(etiqueta=k.upper(), valor=str(v).strip()))
    else:
        filas.append(_FilaResultado(etiqueta="RESULTADO", valor="Sin resultados registrados."))
    return filas


_watermark_png: Optional[io.BytesIO] = None
_WATERMARK_OPACITY = 0.20


def _logo_watermark_buffer() -> Optional[io.BytesIO]:
    """Logo semitransparente como marca de agua (visible al imprimir, poca tinta)."""
    global _watermark_png
    if _watermark_png is not None:
        _watermark_png.seek(0)
        return _watermark_png

    path = _logo_path()
    if not path:
        return None
    try:
        from PIL import Image as PILImage

        img = PILImage.open(path).convert("RGBA")
        r, g, b, a = img.split()
        a = a.point(lambda p: int(p * _WATERMARK_OPACITY))
        img = PILImage.merge("RGBA", (r, g, b, a))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        _watermark_png = buf
        return buf
    except Exception:
        return None


def _draw_logo_watermark(c: canvas.Canvas) -> None:
    buf = _logo_watermark_buffer()
    if not buf:
        return
    width, height = A4
    w, h = 14 * cm, 6.8 * cm
    x = (width - w) / 2
    y = (height - h) / 2 - 0.4 * cm
    c.saveState()
    c.drawImage(ImageReader(buf), x, y, width=w, height=h, mask="auto", preserveAspectRatio=True)
    c.restoreState()


def _draw_page_header_lines(c: canvas.Canvas) -> None:
    width, height = A4
    c.saveState()
    c.setStrokeColor(C_GREEN)
    c.setLineWidth(1.1)
    c.line(1.6 * cm, height - 12 * mm, width - 1.6 * cm, height - 12 * mm)
    c.setStrokeColor(C_YELLOW)
    c.setLineWidth(0.6)
    c.line(1.6 * cm, height - 13.2 * mm, width - 1.6 * cm, height - 13.2 * mm)
    c.restoreState()


def _draw_page_footer(c: canvas.Canvas, doc, meta: dict) -> None:
    width, _height = A4
    footer_y = 18 * mm
    c.saveState()
    c.setStrokeColor(C_SLATE)
    c.setLineWidth(0.5)
    c.line(1.6 * cm, footer_y + 10 * mm, width - 1.6 * cm, footer_y + 10 * mm)

    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(C_BLUE)
    c.drawCentredString(width / 2, footer_y + 6.5 * mm, LAB_CIUDAD)

    c.setFont("Helvetica", 6.5)
    c.setFillColor(C_MUTED)
    c.drawCentredString(width / 2, footer_y + 3.5 * mm, LAB_DIRECCION)
    c.drawCentredString(width / 2, footer_y + 0.8 * mm, f"Tel. {LAB_TELEFONO}  ·  {LAB_EMAIL}  ·  {LAB_WEB}")

    c.setFont("Helvetica", 6.5)
    c.drawString(1.6 * cm, footer_y - 2 * mm, f"Emitido: {meta['fecha_emision']}")
    c.drawRightString(width - 1.6 * cm, footer_y - 2 * mm, f"Pág. {doc.page}")
    if meta.get("codigo"):
        c.drawCentredString(width / 2, footer_y - 2 * mm, meta["codigo"])

    c.setFont("Helvetica-Oblique", 5.5)
    c.setFillColor(colors.HexColor("#94a3b8"))
    c.drawCentredString(
        width / 2,
        footer_y - 5 * mm,
        "Documento electrónico válido sin firma manuscrita · Verifique en línea con el código QR",
    )
    c.restoreState()


def _p(styles, name: str, **kwargs) -> ParagraphStyle:
    base = styles["Normal"]
    return ParagraphStyle(name, parent=base, **kwargs)


def _build_header(story: list, styles, codigo_orden: str) -> None:
    logo = _logo_path()
    contact = Paragraph(
        f"<font size='10' color='#1e40af'><b>INFORME DE RESULTADOS</b></font><br/>"
        f"<font size='8' color='#64748b'>Código: </font>"
        f"<font size='9' color='#059669'><b>{_escape_html(codigo_orden)}</b></font><br/><br/>"
        f"<font size='8'><b>Tel:</b> {LAB_TELEFONO} &nbsp;|&nbsp; <b>Email:</b> {LAB_EMAIL}</font><br/>"
        f"<font size='7' color='#64748b'>Registro habilitación SEDES</font>",
        _p(styles, "HdrContact", fontSize=9, leading=12, alignment=TA_RIGHT, textColor=C_SLATE),
    )

    if logo:
        left = RLImage(logo, width=5.8 * cm, height=2.7 * cm, kind="proportional")
    else:
        left = Paragraph(
            "<font size='20' color='#10b981'><b>GENOTIPIA</b></font><br/>"
            "<font size='11' color='#1e40af'><b>LABORATORIO CLÍNICO</b></font><br/>"
            f"<font size='8' color='#64748b'>{LAB_TAGLINE}</font>",
            _p(styles, "HdrBrand", leading=15, alignment=TA_LEFT),
        )

    hdr = Table([[left, contact]], colWidths=[9.2 * cm, 8.3 * cm])
    hdr.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LINEBELOW", (0, 0), (-1, -1), 1.5, C_YELLOW),
            ]
        )
    )
    story.append(hdr)
    story.append(Spacer(1, 3 * mm))


def _build_paciente_box(story: list, orden: Orden, styles) -> None:
    paciente = orden.paciente
    fc = _to_local(orden.fecha_creacion)
    fcomp = _to_local(orden.fecha_completado) if orden.fecha_completado else fc
    medico = (orden.medico_solicitante or "PARTICULAR").upper()
    centro = "PARTICULAR"
    matricula = str(paciente.id).zfill(5)

    lbl = _p(styles, "PacLbl", fontSize=7.5, textColor=C_BLUE, fontName="Helvetica-Bold")
    val = _p(styles, "PacVal", fontSize=9, textColor=C_SLATE, fontName="Helvetica-Bold", leading=11)
    val_norm = _p(styles, "PacValN", fontSize=8.5, textColor=C_SLATE, leading=11)

    def celda(etiqueta: str, contenido: str, bold: bool = True) -> List[Any]:
        estilo = val if bold else val_norm
        return [
            Paragraph(f"<font color='#1e40af'><b>{etiqueta}</b></font>", lbl),
            Paragraph(_escape_html(contenido), estilo),
        ]

    orden_fecha = Paragraph(
        f"<font color='#059669'><b>{_escape_html(orden.codigo_orden)}</b></font><br/>"
        f"<font size='7.5' color='#64748b'>Ingreso: {fc.strftime('%d/%m/%Y %H:%M')}</font><br/>"
        f"<font size='7.5' color='#64748b'>Informado: {fcomp.strftime('%d/%m/%Y %H:%M')}</font>",
        val_norm,
    )

    col_label = 2.9 * cm
    col_val = 5.85 * cm
    data = [
        celda("PACIENTE", f"{paciente.nombre} {paciente.apellido}".upper())
        + celda("EDAD", _edad_texto(paciente.fecha_nacimiento)),
        celda("CI / ID", paciente.dni, bold=False) + celda("DOCTOR SOLICITANTE", medico),
        celda("CENTRO", centro, bold=False) + celda("MATRÍCULA", matricula, bold=False),
        [
            Paragraph("<font color='#1e40af'><b>ORDEN / FECHA</b></font>", lbl),
            orden_fecha,
            Paragraph("<font color='#1e40af'><b>ESTADO</b></font>", lbl),
            Paragraph("<font color='#059669'><b>COMPLETADO</b></font>", val),
        ],
    ]

    tbl = Table(data, colWidths=[col_label, col_val, col_label, col_val])
    tbl.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, C_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(tbl)
    story.append(Spacer(1, 5 * mm))


def _build_tabla_analitos(filas: List[_FilaResultado], styles) -> Table:
    header_style = _p(styles, "TblH", fontSize=8, fontName="Helvetica-Bold", textColor=C_BLUE, alignment=TA_CENTER)
    cell_style = _p(styles, "TblC", fontSize=8.5, textColor=C_SLATE, alignment=TA_CENTER)
    cell_left = _p(styles, "TblL", fontSize=8.5, textColor=C_SLATE, alignment=TA_LEFT)

    rows: List[List[Any]] = [
        [
            Paragraph("PARÁMETRO", header_style),
            Paragraph("RESULTADO", header_style),
            Paragraph("UNIDAD", header_style),
            Paragraph("REFERENCIA", header_style),
            Paragraph("ESTADO", header_style),
        ]
    ]

    for i, f in enumerate(filas, start=1):
        flag, fcolor = _evaluar_flag(f.valor, f.vmin, f.vmax)
        flag_html = f"<font color='#{fcolor.hexval()[2:]}'><b>{flag}</b></font>" if flag != "—" else flag
        rows.append(
            [
                Paragraph(_escape_html(f.etiqueta.title()), cell_left),
                Paragraph(f"<b><font color='#059669'>{_escape_html(f.valor)}</font></b>", cell_style),
                Paragraph(_escape_html(f.unidad or "—"), cell_style),
                Paragraph(_escape_html(f.ref or "—"), cell_style),
                Paragraph(flag_html, cell_style),
            ]
        )

    col_widths = [5.2 * cm, 2.8 * cm, 2.2 * cm, 3.5 * cm, 2.3 * cm]
    tbl = Table(rows, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return tbl


def _build_bloque_narrativo(filas: List[_FilaResultado], styles) -> List[Any]:
    bloques: List[Any] = []
    label_style = _p(
        styles,
        "NarLbl",
        fontSize=9,
        fontName="Helvetica-Bold",
        textColor=C_GREEN,
        spaceAfter=2,
    )
    body_style = _p(
        styles,
        "NarBody",
        fontSize=9.5,
        textColor=C_SLATE,
        leading=14,
        alignment=TA_JUSTIFY,
        leftIndent=0,
        spaceAfter=6,
    )

    for f in filas:
        ref_txt = f" <font size='7' color='#64748b'><i>(Ref: {_escape_html(f.ref)})</i></font>" if f.ref else ""
        if len(f.valor) > 60 or f.tipo.lower() == "texto area":
            bloques.append(Paragraph(f"<b>{_escape_html(f.etiqueta)}</b>", label_style))
            bloques.append(Paragraph(_escape_html(f.valor) + ref_txt, body_style))
        else:
            bloques.append(
                Paragraph(
                    f"<b>{_escape_html(f.etiqueta)}:</b> {_escape_html(f.valor)}{ref_txt}",
                    body_style,
                )
            )
    return bloques


def _build_examen_seccion(res, styles) -> List[Any]:
    examen = res.examen
    if not examen:
        return []
    filas = _filas_resultado_examen(res)
    tabla_filas = [f for f in filas if f.es_tabla]
    texto_filas = [f for f in filas if not f.es_tabla]

    cuerpo: List[Any] = [
        Spacer(1, 3 * mm),
        Paragraph(
            f"<font color='#059669'><b>{_escape_html(examen.nombre.upper())}</b></font>",
            _p(styles, "ExamTitle", fontSize=11, spaceAfter=4, fontName="Helvetica-Bold"),
        ),
    ]

    if tabla_filas:
        cuerpo.append(_build_tabla_analitos(tabla_filas, styles))
        cuerpo.append(Spacer(1, 2 * mm))

    if texto_filas:
        cuerpo.extend(_build_bloque_narrativo(texto_filas, styles))

    cuerpo.append(Spacer(1, 4 * mm))
    return cuerpo


def _build_validacion(story: list, firmante: str, codigo: str, fecha: datetime, styles) -> None:
    firma_style = _p(styles, "Firma", fontSize=9, alignment=TA_CENTER, textColor=C_SLATE, leading=12)
    stamp_style = _p(
        styles,
        "Stamp",
        fontSize=7,
        alignment=TA_CENTER,
        textColor=C_MUTED,
        borderWidth=1,
        borderColor=C_BORDER,
        borderPadding=8,
    )

    firma = Paragraph(
        f"<font color='#059669'><b>VALIDADO POR</b></font><br/><br/>"
        f"<font color='#1e40af'><b>{_escape_html(firmante)}</b></font><br/>"
        f"Bioquímica responsable<br/><br/>"
        f"<font size='8' color='#64748b'>Informado el {_fmt_fecha_hora(fecha)}</font>",
        firma_style,
    )

    qr_bytes = qr_service.generar_qr_png(qr_service.url_resultados_orden(codigo))
    qr_img = RLImage(io.BytesIO(qr_bytes), width=2.8 * cm, height=2.8 * cm)
    qr_block = Table(
        [
            [qr_img],
            [
                Paragraph(
                    "<b>Consulta en línea</b><br/>"
                    "<font size='6'>Escanee para verificar<br/>sus resultados</font>",
                    _p(styles, "QrLbl", fontSize=7, alignment=TA_CENTER, textColor=C_SLATE),
                )
            ],
        ],
        colWidths=[3.2 * cm],
    )
    qr_block.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BOX", (0, 0), (-1, -1), 0.6, C_BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    sello = Paragraph(
        "<font color='#10b981'><b>GENOTIPIA</b></font><br/>"
        "<font color='#1e40af'>Laboratorio Clínico</font><br/>"
        "Santa Cruz — Bolivia",
        stamp_style,
    )

    row = Table([[firma, sello, qr_block]], colWidths=[7.5 * cm, 5.5 * cm, 4.5 * cm])
    row.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("ALIGN", (2, 0), (2, 0), "RIGHT"),
                ("BOX", (0, 0), (-1, -1), 0.6, C_BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(Spacer(1, 4 * mm))
    story.append(row)


class _InformeDocTemplate(SimpleDocTemplate):
    """Plantilla con marca de agua encima del contenido y pie al final de página."""

    def __init__(self, *args, pdf_meta: Optional[dict] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.pdf_meta = pdf_meta or {}

    def handle_pageEnd(self):
        _draw_logo_watermark(self.canv)
        _draw_page_footer(self.canv, self, self.pdf_meta)
        super().handle_pageEnd()


def generar_informe_orden(orden: Orden, firmante_nombre: str) -> str:
    """Genera PDF profesional y devuelve la ruta absoluta del archivo."""
    path = ruta_informe(orden.codigo_orden)
    fecha_informe = datetime.now(_get_tz())
    meta = {
        "fecha_emision": _fmt_fecha_hora(fecha_informe),
        "codigo": orden.codigo_orden,
    }

    doc = _InformeDocTemplate(
        path,
        pagesize=A4,
        rightMargin=1.6 * cm,
        leftMargin=1.6 * cm,
        topMargin=1.2 * cm,
        bottomMargin=2.8 * cm,
        title=f"Informe {orden.codigo_orden}",
        pdf_meta=meta,
    )

    styles = getSampleStyleSheet()
    story: list = []

    _build_header(story, styles, orden.codigo_orden)
    _build_paciente_box(story, orden, styles)

    examenes_titulo = Paragraph(
        '<font color="#1e40af"><b>RESULTADOS DE ANÁLISIS</b></font>',
        _p(styles, "SecTitle", fontSize=10, spaceAfter=4, fontName="Helvetica-Bold"),
    )
    story.append(examenes_titulo)
    story.append(Spacer(1, 2 * mm))

    for res in orden.resultados:
        story.extend(_build_examen_seccion(res, styles))

    _build_validacion(story, firmante_nombre, orden.codigo_orden, fecha_informe, styles)

    def _on_page_begin(c: canvas.Canvas, d) -> None:
        _draw_page_header_lines(c)

    doc.build(story, onFirstPage=_on_page_begin, onLaterPages=_on_page_begin)
    return path
