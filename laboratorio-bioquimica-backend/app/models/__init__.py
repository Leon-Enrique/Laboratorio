from app.db.session import Base
from app.models.usuario import Usuario, Paciente
from app.models.examen import Examen, FormulaConsumo
from app.models.parametro_examen import ParametroExamen
from app.models.inventario import Proveedor, Reactivo, MovimientoStock, Lote
from app.models.orden import Orden, Resultado

# Todos los modelos se heredan de Base.
# Esto nos ayuda a que Alembic los importe de forma centralizada.
__all__ = [
    "Base",
    "Usuario",
    "Paciente",
    "Examen",
    "FormulaConsumo",
    "ParametroExamen",
    "Proveedor",
    "Reactivo",
    "Lote",
    "MovimientoStock",
    "Orden",
    "Resultado"
]
