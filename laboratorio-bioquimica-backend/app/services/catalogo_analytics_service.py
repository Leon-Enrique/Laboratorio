from typing import List

from sqlalchemy.orm import Session

from app.models.examen import Examen
from app.models.examen_busqueda_stat import ExamenBusquedaStat
from app.schemas.catalogo_analytics import MasBuscadoResponse


def _get_or_create_stat(db: Session, examen_id: int) -> ExamenBusquedaStat:
    stat = db.query(ExamenBusquedaStat).filter(ExamenBusquedaStat.examen_id == examen_id).first()
    if stat:
        return stat
    stat = ExamenBusquedaStat(examen_id=examen_id)
    db.add(stat)
    return stat


def registrar_busqueda_catalogo(db: Session, termino: str, examen_ids: List[int]) -> int:
    """Incrementa contador de búsqueda para exámenes visibles que coincidieron."""
    del termino  # reservado para futuro ranking por término
    ids_validos = {
        row.id
        for row in db.query(Examen.id)
        .filter(Examen.id.in_(examen_ids), Examen.visible == True)
        .all()
    }
    now = ExamenBusquedaStat.now_utc()
    actualizados = 0
    for examen_id in ids_validos:
        stat = _get_or_create_stat(db, examen_id)
        stat.contador_busquedas = (stat.contador_busquedas or 0) + 1
        stat.ultima_busqueda = now
        actualizados += 1
    db.commit()
    return actualizados


def registrar_clic_catalogo(db: Session, examen_id: int) -> bool:
    examen = db.query(Examen).filter(Examen.id == examen_id, Examen.visible == True).first()
    if not examen:
        return False
    stat = _get_or_create_stat(db, examen_id)
    stat.contador_clics = (stat.contador_clics or 0) + 1
    stat.ultimo_clic = ExamenBusquedaStat.now_utc()
    db.commit()
    return True


def listar_mas_buscados(db: Session, limite: int = 10) -> List[MasBuscadoResponse]:
    rows = (
        db.query(ExamenBusquedaStat, Examen)
        .join(Examen, Examen.id == ExamenBusquedaStat.examen_id)
        .filter(Examen.visible == True)
        .all()
    )
    ranking: List[MasBuscadoResponse] = []
    for stat, examen in rows:
        busquedas = stat.contador_busquedas or 0
        clics = stat.contador_clics or 0
        if busquedas == 0 and clics == 0:
            continue
        ranking.append(
            MasBuscadoResponse(
                examen_id=examen.id,
                nombre=examen.nombre,
                grupo=examen.grupo,
                contador_busquedas=busquedas,
                contador_clics=clics,
                puntuacion=busquedas + clics * 2,
                ya_destacado=bool(examen.destacado),
                visible=bool(examen.visible),
            )
        )
    ranking.sort(key=lambda item: (-item.puntuacion, -item.contador_clics, item.nombre))
    return ranking[:limite]
