from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.db.session import get_db
from app.models.examen import Examen, FormulaConsumo
from app.schemas.examen import ExamenResponse, ExamenCreate
from app.api.v1.endpoints.auth import RoleChecker
from app.services import parametros_service as param_svc

router = APIRouter()

def _examenes_query(db: Session):
    return db.query(Examen).options(
        joinedload(Examen.formulas),
        joinedload(Examen.parametros),
    )

# Catálogo público: cualquiera puede listar los exámenes visibles
@router.get("/", response_model=List[ExamenResponse])
def listar_examenes(db: Session = Depends(get_db)) -> Any:
    return _examenes_query(db).filter(Examen.visible == True).order_by(Examen.id).all()

# Catálogo administrativo: muestra todos los exámenes, visibles o no (solo admin/bioquímico)
@router.get("/admin-lista", response_model=List[ExamenResponse])
def listar_examenes_admin(
    db: Session = Depends(get_db),
    current_user: Any = Depends(RoleChecker(["admin", "bioquimico"]))
) -> Any:
    return _examenes_query(db).order_by(Examen.id).all()

# Cambiar visibilidad del examen (solo admin)
@router.put("/{examen_id}/visibilidad", response_model=ExamenResponse)
def toggle_visibilidad_examen(
    examen_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(RoleChecker(["admin"]))
) -> Any:
    examen = db.query(Examen).filter(Examen.id == examen_id).first()
    if not examen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Examen no encontrado"
        )
    # Alternar visibilidad
    examen.visible = not examen.visible
    db.add(examen)
    db.commit()
    return _examenes_query(db).filter(Examen.id == examen_id).first()

# Crear examen con su fórmula BOM (solo admin/bioquímico)
@router.post("/", response_model=ExamenResponse)
def crear_examen(
    examen_in: ExamenCreate, 
    db: Session = Depends(get_db),
    current_user: Any = Depends(RoleChecker(["admin", "bioquimico"]))
) -> Any:
    db_examen = db.query(Examen).filter(Examen.nombre == examen_in.nombre).first()
    if db_examen:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un examen con este nombre"
        )
    
    nuevo_examen = Examen(
        nombre=examen_in.nombre,
        descripcion=examen_in.descripcion,
        preparacion=examen_in.preparacion,
        precio_usd=examen_in.precio_usd,
        tiempo_entrega_horas=examen_in.tiempo_entrega_horas,
        visible=examen_in.visible if examen_in.visible is not None else True
    )
    db.add(nuevo_examen)
    db.commit()
    db.refresh(nuevo_examen)

    # Insertar fórmula de consumo (BOM) asociada si fue provista
    if examen_in.formulas:
        for f_item in examen_in.formulas:
            formula = FormulaConsumo(
                examen_id=nuevo_examen.id,
                reactivo_id=f_item.reactivo_id,
                cantidad_consumo=f_item.cantidad_consumo
            )
            db.add(formula)
        db.commit()

    if examen_in.parametros:
        param_svc.guardar_parametros_examen(db, nuevo_examen.id, examen_in.parametros)
        db.commit()

    db.refresh(nuevo_examen)
    return _examenes_query(db).filter(Examen.id == nuevo_examen.id).first()

# Actualizar examen con su fórmula BOM (solo admin)
@router.put("/{examen_id}", response_model=ExamenResponse)
def actualizar_examen(
    examen_id: int,
    examen_in: ExamenCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(RoleChecker(["admin"]))
) -> Any:
    examen = db.query(Examen).filter(Examen.id == examen_id).first()
    if not examen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Examen no encontrado"
        )
    
    # Validar duplicados si cambia el nombre
    if examen_in.nombre != examen.nombre:
        db_examen = db.query(Examen).filter(Examen.nombre == examen_in.nombre).first()
        if db_examen:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe otro examen con este nombre"
            )
            
    # Actualizar campos
    examen.nombre = examen_in.nombre
    examen.descripcion = examen_in.descripcion
    examen.preparacion = examen_in.preparacion
    examen.precio_usd = examen_in.precio_usd
    examen.tiempo_entrega_horas = examen_in.tiempo_entrega_horas
    if examen_in.visible is not None:
        examen.visible = examen_in.visible
        
    # Eliminar fórmulas viejas e insertar nuevas
    db.query(FormulaConsumo).filter(FormulaConsumo.examen_id == examen_id).delete()
    
    if examen_in.formulas:
        for f_item in examen_in.formulas:
            formula = FormulaConsumo(
                examen_id=examen_id,
                reactivo_id=f_item.reactivo_id,
                cantidad_consumo=f_item.cantidad_consumo
            )
            db.add(formula)

    param_svc.guardar_parametros_examen(db, examen_id, examen_in.parametros or [])
            
    db.add(examen)
    db.commit()
    return _examenes_query(db).filter(Examen.id == examen_id).first()
