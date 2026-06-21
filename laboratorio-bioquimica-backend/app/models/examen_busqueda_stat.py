from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db.session import Base


class ExamenBusquedaStat(Base):
    """Contadores anónimos de búsquedas y clics en el catálogo público."""

    __tablename__ = "examen_busqueda_stats"

    examen_id = Column(Integer, ForeignKey("examenes.id", ondelete="CASCADE"), primary_key=True)
    contador_busquedas = Column(Integer, default=0, nullable=False)
    contador_clics = Column(Integer, default=0, nullable=False)
    ultima_busqueda = Column(DateTime(timezone=True), nullable=True)
    ultimo_clic = Column(DateTime(timezone=True), nullable=True)

    examen = relationship("Examen", backref="busqueda_stat")

    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(timezone.utc)
