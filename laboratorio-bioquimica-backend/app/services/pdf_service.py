"""Generación de informes PDF clínicos con ReportLab."""
from __future__ import annotations

import os
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models.orden import Orden

TZ_LAB = "America/La_Paz"


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


def _parametro_clave(nombre: str, unidad: Optional[str]) -> str:
    return f"{nombre} ({unidad})" if unidad else nombre


def _evaluar_flag(valor_str: str, vmin: Optional[float], vmax: Optional[float]) -> str:
    try:
        valor = float(str(valor_str).replace(",", ".").strip())
    except (TypeError, ValueError):
        return "—"
    if vmin is not None and valor < vmin:
        return "Bajo"
    if vmax is not None and valor > vmax:
        return "Alto"
    return "Normal"


def _obtener_valor(valores: dict, nombre: str, unidad: Optional[str]) -> str:
    """Busca el valor guardado probando varias claves (compatibilidad legacy)."""
    if not valores:
        return "—"
    claves = [
        _parametro_clave(nombre, unidad),
        nombre,
        f"{nombre} ({unidad})" if unidad else nombre,
    ]
    for k in claves:
        if k in valores and valores[k] is not None and str(valores[k]).strip() != "":
            return str(valores[k]).strip()
    # Búsqueda flexible por nombre parcial
    nombre_lower = nombre.lower()
    for k, v in valores.items():
        if v is not None and str(v).strip() and nombre_lower in k.lower():
            return str(v).strip()
    return "—"


def generar_informe_orden(orden: Orden, firmante_nombre: str) -> str:
    """Genera PDF y devuelve la ruta absoluta del archivo."""
    path = ruta_informe(orden.codigo_orden)
    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Informe {orden.codigo_orden}",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "GenotipiaTitle",
        parent=styles["Heading1"],
        fontSize=22,
        textColor=colors.HexColor("#059669"),
        spaceAfter=6,
        alignment=1,
    )
    subtitle_style = ParagraphStyle(
        "GenotipiaSub",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#475569"),
        alignment=1,
        spaceAfter=14,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=11,
        textColor=colors.HexColor("#334155"),
        spaceBefore=12,
        spaceAfter=6,
    )

    story = []
    story.append(Paragraph("<b>GENOTIPIA</b>", title_style))
    story.append(Paragraph("Laboratorio Clínico · Santa Cruz, Bolivia", subtitle_style))
    story.append(Paragraph("INFORME DE RESULTADOS CLÍNICOS", section_style))

    fc = orden.fecha_completado or orden.fecha_creacion
    if fc.tzinfo is None:
        fc_local = fc.replace(tzinfo=_get_tz())
    else:
        fc_local = fc.astimezone(_get_tz())
    fecha_txt = fc_local.strftime("%d/%m/%Y %H:%M")

    paciente = orden.paciente
    info_data = [
        ["Código de orden", orden.codigo_orden],
        ["Fecha de emisión", fecha_txt],
        ["Paciente", f"{paciente.nombre} {paciente.apellido}"],
        ["CI / Identificación", paciente.dni],
        ["Fecha de nacimiento", paciente.fecha_nacimiento.strftime("%d/%m/%Y")],
        ["Bioquímico firmante", firmante_nombre],
        ["Estado", "COMPLETADO Y FIRMADO"],
    ]
    info_table = Table(info_data, colWidths=[5 * cm, 12 * cm])
    info_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#64748b")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(info_table)
    story.append(Spacer(1, 0.4 * cm))

    # Resumen de análisis solicitados
    nombres_examenes = [res.examen.nombre for res in orden.resultados if res.examen]
    if nombres_examenes:
        story.append(Paragraph("<b>Análisis realizados</b>", section_style))
        lista = " · ".join(nombres_examenes)
        story.append(
            Paragraph(
                lista,
                ParagraphStyle("ExamList", parent=styles["Normal"], fontSize=9, spaceAfter=10),
            )
        )

    for res in orden.resultados:
        examen = res.examen
        if not examen:
            continue
        story.append(Paragraph(f"<b>{examen.nombre}</b>", section_style))
        if examen.descripcion:
            story.append(
                Paragraph(
                    f"<i>{examen.descripcion}</i>",
                    ParagraphStyle("ExamDesc", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#64748b"), spaceAfter=4),
                )
            )

        rows = [["Parámetro", "Resultado", "Unidad", "Referencia", "Estado"]]
        parametros = sorted(examen.parametros, key=lambda p: p.orden) if examen.parametros else []
        valores = res.valor_resultado or {}
        claves_usadas = set()

        if parametros:
            for p in parametros:
                clave = _parametro_clave(p.nombre, p.unidad)
                val = _obtener_valor(valores, p.nombre, p.unidad)
                claves_usadas.add(clave)
                claves_usadas.add(p.nombre)
                ref = ""
                if p.valor_min is not None and p.valor_max is not None:
                    ref = f"{p.valor_min:g} – {p.valor_max:g}"
                elif p.valor_max is not None:
                    ref = f"≤ {p.valor_max:g}"
                elif p.valor_min is not None:
                    ref = f"≥ {p.valor_min:g}"
                flag = _evaluar_flag(val, p.valor_min, p.valor_max)
                rows.append([p.nombre, val, p.unidad or "—", ref or "—", flag])
            # Valores legacy no mapeados a parámetros del catálogo
            for k, v in valores.items():
                if k in claves_usadas or v is None or str(v).strip() == "":
                    continue
                rows.append([k, str(v).strip(), "—", "—", "—"])
        elif valores:
            for k, v in valores.items():
                rows.append([k, str(v), "—", "—", "—"])
        else:
            rows.append(["Sin resultados", "—", "—", "—", "—"])

        tbl = Table(rows, colWidths=[4.5 * cm, 3 * cm, 2 * cm, 3.5 * cm, 2.5 * cm])
        tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(tbl)
        story.append(Spacer(1, 0.3 * cm))

    story.append(Spacer(1, 0.8 * cm))
    story.append(
        Paragraph(
            f"<i>Documento generado electrónicamente el {datetime.now(_get_tz()).strftime('%d/%m/%Y %H:%M')} "
            f"(hora Bolivia). Válido sin firma manuscrita.</i>",
            ParagraphStyle("Footer", parent=styles["Normal"], fontSize=7, textColor=colors.grey),
        )
    )

    doc.build(story)
    return path
