from collections import defaultdict
from datetime import datetime, timezone, date, timedelta, time
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session, joinedload

from app.models.orden import Orden, Resultado
from app.models.examen import Examen
from app.models.inventario import Reactivo
from app.models.usuario import Paciente
from app.schemas.reportes import (
    DashboardReporte,
    MesDestacado,
    MesReporte,
    MovimientoDia,
    PuntoSerie,
    ReporteDiario,
    ResumenDia,
    ResumenMesActual,
    ResumenPeriodo,
    TopExamenMes,
)

MESES_ES = (
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
)
MESES_CORTO = ("Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic")

# Bolivia no usa horario de verano; UTC-4 fijo como respaldo si falta tzdata (p. ej. Windows).
TZ_LABORATORIO = timezone(timedelta(hours=-4))


def _get_tz(tz_name: str = "America/La_Paz"):
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        return TZ_LABORATORIO


def _to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _month_key(dt: Optional[datetime]) -> Optional[Tuple[int, int]]:
    dt = _to_utc(dt)
    if dt is None:
        return None
    return dt.year, dt.month


def _etiqueta_mes(anio: int, mes: int) -> str:
    return f"{MESES_ES[mes - 1]} {anio}"


def _etiqueta_corta(anio: int, mes: int) -> str:
    return f"{MESES_CORTO[mes - 1]} {str(anio)[2:]}"


def precio_orden(orden: Orden) -> float:
    return sum(r.examen.precio_bob for r in orden.resultados if r.examen)


def _empty_bucket() -> Dict[str, float]:
    return {
        "ordenes_entradas": 0,
        "ordenes_completadas": 0,
        "ingresos_entradas": 0.0,
        "ingresos_completadas": 0.0,
    }


def _pct_change(actual: float, anterior: float) -> Optional[float]:
    if anterior == 0:
        return 100.0 if actual > 0 else 0.0
    return round(((actual - anterior) / anterior) * 100, 1)


def _etiqueta_fecha(fecha: date) -> str:
    return f"{fecha.day} de {MESES_ES[fecha.month - 1]} de {fecha.year}"


def _day_bounds_utc(fecha: date, tz_name: str = "America/La_Paz") -> Tuple[datetime, datetime]:
    tz = _get_tz(tz_name)
    start_local = datetime.combine(fecha, time.min, tzinfo=tz)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def _hora_local_texto(dt: Optional[datetime], tz_name: str = "America/La_Paz") -> str:
    dt = _to_utc(dt)
    if dt is None:
        return "—"
    local = dt.astimezone(_get_tz(tz_name))
    return local.strftime("%H:%M")


def _nombres_examenes(orden: Orden) -> List[str]:
    return [r.examen.nombre for r in orden.resultados if r.examen]


def _nombre_paciente(orden: Orden) -> str:
    if not orden.paciente:
        return "—"
    return f"{orden.paciente.nombre} {orden.paciente.apellido}".strip()


def generar_reporte_dia(
    db: Session,
    fecha: date,
    tipo: str = "todos",
    tz_name: str = "America/La_Paz",
) -> ReporteDiario:
    start_utc, end_utc = _day_bounds_utc(fecha, tz_name)

    ordenes = (
        db.query(Orden)
        .options(
            joinedload(Orden.paciente),
            joinedload(Orden.resultados).joinedload(Resultado.examen),
        )
        .all()
    )

    movimientos: List[MovimientoDia] = []
    resumen = ResumenDia(
        fecha=fecha,
        etiqueta_fecha=_etiqueta_fecha(fecha),
    )

    for orden in ordenes:
        precio = precio_orden(orden)
        fc = _to_utc(orden.fecha_creacion)
        paciente = _nombre_paciente(orden)
        examenes = _nombres_examenes(orden)

        if fc and start_utc <= fc < end_utc and tipo in ("todos", "entradas"):
            movimientos.append(
                MovimientoDia(
                    tipo="ENTRADA",
                    hora=fc,
                    hora_texto=_hora_local_texto(fc, tz_name),
                    orden_id=orden.id,
                    codigo_orden=orden.codigo_orden,
                    paciente=paciente,
                    monto=round(precio, 2),
                    estado_orden=orden.estado,
                    estado_pago=orden.estado_pago or "PENDIENTE",
                    metodo_pago=orden.metodo_pago,
                    examenes=examenes,
                )
            )
            resumen.entradas += 1
            resumen.ingresos_entradas += precio
            if (orden.estado_pago or "PENDIENTE") == "PAGADO":
                resumen.cobrado_dia += precio
            else:
                resumen.pendiente_dia += precio

        if orden.estado == "COMPLETADO" and tipo in ("todos", "salidas"):
            fcomp = _to_utc(orden.fecha_completado) or fc
            if fcomp and start_utc <= fcomp < end_utc:
                movimientos.append(
                    MovimientoDia(
                        tipo="SALIDA",
                        hora=fcomp,
                        hora_texto=_hora_local_texto(fcomp, tz_name),
                        orden_id=orden.id,
                        codigo_orden=orden.codigo_orden,
                        paciente=paciente,
                        monto=round(precio, 2),
                        estado_orden=orden.estado,
                        estado_pago=orden.estado_pago or "PENDIENTE",
                        metodo_pago=orden.metodo_pago,
                        examenes=examenes,
                    )
                )
                resumen.salidas += 1
                resumen.ingresos_salidas += precio

    movimientos.sort(key=lambda m: m.hora)
    resumen.ingresos_entradas = round(resumen.ingresos_entradas, 2)
    resumen.ingresos_salidas = round(resumen.ingresos_salidas, 2)
    resumen.cobrado_dia = round(resumen.cobrado_dia, 2)
    resumen.pendiente_dia = round(resumen.pendiente_dia, 2)

    return ReporteDiario(moneda="BOB", resumen=resumen, movimientos=movimientos)


def _punto_desde_bucket(etiqueta: str, b: Dict[str, float]) -> PuntoSerie:
    return PuntoSerie(
        etiqueta=etiqueta,
        ordenes_entradas=int(b["ordenes_entradas"]),
        ordenes_completadas=int(b["ordenes_completadas"]),
        ingresos_entradas=round(b["ingresos_entradas"], 2),
        ingresos_completadas=round(b["ingresos_completadas"], 2),
    )


def _build_serie_diaria(day_buckets: Dict[date, Dict[str, float]], hoy: date, dias: int = 7) -> List[PuntoSerie]:
    serie: List[PuntoSerie] = []
    for offset in range(dias - 1, -1, -1):
        d = hoy - timedelta(days=offset)
        b = day_buckets.get(d, _empty_bucket())
        serie.append(_punto_desde_bucket(d.strftime("%d/%m"), b))
    return serie


def _build_serie_semanal(
    week_buckets: Dict[Tuple[int, int], Dict[str, float]], hoy: date, semanas: int = 8
) -> List[PuntoSerie]:
    tz = _get_tz()
    base = datetime.combine(hoy, time.min, tzinfo=tz)
    serie: List[PuntoSerie] = []
    for offset in range(semanas - 1, -1, -1):
        dt = base - timedelta(weeks=offset)
        iso = dt.isocalendar()
        key = (iso.year, iso.week)
        b = week_buckets.get(key, _empty_bucket())
        serie.append(_punto_desde_bucket(f"Sem {iso.week}", b))
    return serie


def generar_dashboard(db: Session, meses_historial: int = 12) -> DashboardReporte:
    ordenes = (
        db.query(Orden)
        .options(joinedload(Orden.resultados).joinedload(Resultado.examen))
        .all()
    )

    hoy = datetime.now(timezone.utc).date()
    mes_actual = (hoy.year, hoy.month)

    buckets: Dict[Tuple[int, int], Dict[str, float]] = defaultdict(_empty_bucket)
    day_buckets: Dict[date, Dict[str, float]] = defaultdict(_empty_bucket)
    week_buckets: Dict[Tuple[int, int], Dict[str, float]] = defaultdict(_empty_bucket)
    resumen_hoy = ResumenPeriodo()
    examenes_mes: Dict[int, Dict] = defaultdict(lambda: {"cantidad": 0, "ingresos": 0.0, "nombre": ""})
    pendientes_total = 0
    pendientes_mes_actual = 0

    for orden in ordenes:
        precio = precio_orden(orden)
        fc = _to_utc(orden.fecha_creacion)
        key_entrada = _month_key(fc)

        if key_entrada:
            buckets[key_entrada]["ordenes_entradas"] += 1
            buckets[key_entrada]["ingresos_entradas"] += precio

        if fc:
            local_day = fc.astimezone(_get_tz()).date()
            day_buckets[local_day]["ordenes_entradas"] += 1
            day_buckets[local_day]["ingresos_entradas"] += precio
            iso = fc.astimezone(_get_tz()).isocalendar()
            week_buckets[(iso.year, iso.week)]["ordenes_entradas"] += 1
            week_buckets[(iso.year, iso.week)]["ingresos_entradas"] += precio

        if fc and fc.date() == hoy:
            resumen_hoy.ordenes_entradas += 1
            resumen_hoy.ingresos_entradas += precio

        if orden.estado != "COMPLETADO":
            pendientes_total += 1
            if key_entrada == mes_actual:
                pendientes_mes_actual += 1
            continue

        fcomp = _to_utc(orden.fecha_completado) or fc
        key_salida = _month_key(fcomp)
        if key_salida:
            buckets[key_salida]["ordenes_completadas"] += 1
            buckets[key_salida]["ingresos_completadas"] += precio

        if fcomp:
            local_day = fcomp.astimezone(_get_tz()).date()
            day_buckets[local_day]["ordenes_completadas"] += 1
            day_buckets[local_day]["ingresos_completadas"] += precio
            iso = fcomp.astimezone(_get_tz()).isocalendar()
            week_buckets[(iso.year, iso.week)]["ordenes_completadas"] += 1
            week_buckets[(iso.year, iso.week)]["ingresos_completadas"] += precio

        if fcomp and fcomp.date() == hoy:
            resumen_hoy.ordenes_completadas += 1
            resumen_hoy.ingresos_completadas += precio

        if key_entrada == mes_actual:
            for res in orden.resultados:
                if not res.examen:
                    continue
                eid = res.examen_id
                examenes_mes[eid]["cantidad"] += 1
                examenes_mes[eid]["ingresos"] += res.examen.precio_bob
                examenes_mes[eid]["nombre"] = res.examen.nombre

    # Últimos N meses (incluye mes actual)
    meses_lista: List[Tuple[int, int]] = []
    y, m = mes_actual
    for _ in range(meses_historial):
        meses_lista.append((y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    meses_lista.reverse()

    meses_reporte: List[MesReporte] = []
    for anio, mes in meses_lista:
        b = buckets.get((anio, mes), _empty_bucket())
        meses_reporte.append(
            MesReporte(
                anio=anio,
                mes=mes,
                etiqueta=_etiqueta_mes(anio, mes),
                etiqueta_corta=_etiqueta_corta(anio, mes),
                ordenes_entradas=int(b["ordenes_entradas"]),
                ordenes_completadas=int(b["ordenes_completadas"]),
                ingresos_entradas=round(b["ingresos_entradas"], 2),
                ingresos_completadas=round(b["ingresos_completadas"], 2),
            )
        )

    actual = meses_reporte[-1] if meses_reporte else None
    anterior = meses_reporte[-2] if len(meses_reporte) > 1 else None

    resumen_mes = ResumenMesActual(
        anio=mes_actual[0],
        mes=mes_actual[1],
        etiqueta=_etiqueta_mes(mes_actual[0], mes_actual[1]),
        ordenes_entradas=actual.ordenes_entradas if actual else 0,
        ordenes_completadas=actual.ordenes_completadas if actual else 0,
        ingresos_entradas=actual.ingresos_entradas if actual else 0,
        ingresos_completadas=actual.ingresos_completadas if actual else 0,
        pendientes_del_mes=pendientes_mes_actual,
        ticket_promedio=round(
            (actual.ingresos_entradas / actual.ordenes_entradas) if actual and actual.ordenes_entradas else 0,
            2,
        ),
        variacion_ordenes_pct=_pct_change(
            actual.ordenes_entradas if actual else 0,
            anterior.ordenes_entradas if anterior else 0,
        )
        if anterior
        else None,
        variacion_ingresos_pct=_pct_change(
            actual.ingresos_entradas if actual else 0,
            anterior.ingresos_entradas if anterior else 0,
        )
        if anterior
        else None,
    )

    top_examenes: List[TopExamenMes] = []
    for eid, data in sorted(examenes_mes.items(), key=lambda x: x[1]["cantidad"], reverse=True)[:5]:
        top_examenes.append(
            TopExamenMes(
                examen_id=eid,
                nombre=data["nombre"] or f"Examen #{eid}",
                cantidad=int(data["cantidad"]),
                ingresos=round(data["ingresos"], 2),
            )
        )

    con_ordenes = [mr for mr in meses_reporte if mr.ordenes_entradas > 0]
    mejor = peor = None
    if con_ordenes:
        mejor_mr = max(con_ordenes, key=lambda x: x.ordenes_entradas)
        peor_mr = min(con_ordenes, key=lambda x: x.ordenes_entradas)
        mejor = MesDestacado(
            etiqueta=mejor_mr.etiqueta,
            anio=mejor_mr.anio,
            mes=mejor_mr.mes,
            ordenes=mejor_mr.ordenes_entradas,
            ingresos=mejor_mr.ingresos_entradas,
        )
        peor = MesDestacado(
            etiqueta=peor_mr.etiqueta,
            anio=peor_mr.anio,
            mes=peor_mr.mes,
            ordenes=peor_mr.ordenes_entradas,
            ingresos=peor_mr.ingresos_entradas,
        )

    return DashboardReporte(
        moneda="BOB",
        resumen_hoy=ResumenPeriodo(
            ordenes_entradas=resumen_hoy.ordenes_entradas,
            ordenes_completadas=resumen_hoy.ordenes_completadas,
            ingresos_entradas=round(resumen_hoy.ingresos_entradas, 2),
            ingresos_completadas=round(resumen_hoy.ingresos_completadas, 2),
        ),
        resumen_mes_actual=resumen_mes,
        pendientes_total=pendientes_total,
        total_examenes=db.query(Examen).filter(Examen.visible == True).count(),
        total_pacientes=db.query(Paciente).count(),
        total_reactivos=db.query(Reactivo).count(),
        meses=meses_reporte,
        serie_diaria=_build_serie_diaria(day_buckets, hoy),
        serie_semanal=_build_serie_semanal(week_buckets, hoy),
        top_examenes_mes=top_examenes,
        mejor_mes=mejor,
        peor_mes=peor,
    )
