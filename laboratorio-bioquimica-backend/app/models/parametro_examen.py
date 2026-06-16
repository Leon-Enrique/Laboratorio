from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base


class ParametroExamen(Base):
    """Parámetro analítico de un examen (nombre, unidad, rango de referencia)."""
    __tablename__ = "parametros_examen"

    id = Column(Integer, primary_key=True, index=True)
    examen_id = Column(Integer, ForeignKey("examenes.id", ondelete="CASCADE"), nullable=False)
    nombre = Column(String, nullable=False)
    unidad = Column(String, nullable=True)
    valor_min = Column(Float, nullable=True)
    valor_max = Column(Float, nullable=True)
    orden = Column(Integer, default=0)

    examen = relationship("Examen", back_populates="parametros")
