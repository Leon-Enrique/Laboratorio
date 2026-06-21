from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.session import Base

class Examen(Base):
    __tablename__ = "examenes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True, nullable=False)
    descripcion = Column(String, nullable=True)
    preparacion = Column(String, nullable=True)  # Indicaciones de ayuno, etc.
    precio_bob = Column(Float, nullable=False)
    tiempo_entrega_horas = Column(Integer, default=24)
    visible = Column(Boolean, default=True)
    destacado = Column(Boolean, default=False)
    titulo_destacado = Column(String, nullable=True)
    subtitulo_destacado = Column(String, nullable=True)
    descripcion_destacado = Column(String, nullable=True)
    orden_destacado = Column(Integer, nullable=True)
    tipo = Column(String, default="Laboratorio")
    grupo = Column(String, nullable=True)
    grupo_impresion = Column(String, nullable=True)
    derivacion = Column(String, nullable=True)
    material_muestra = Column(String, nullable=True)
    estado = Column(String, default="Activo")
    codigo_abrev = Column(String, nullable=True)
    precio_derivacion = Column(Float, default=0)
    etiqueta = Column(String, nullable=True)

    parametros = relationship(
        "ParametroExamen",
        back_populates="examen",
        cascade="all, delete-orphan",
        order_by="ParametroExamen.orden",
    )
    formulas = relationship("FormulaConsumo", back_populates="examen", cascade="all, delete-orphan")
    resultados = relationship("Resultado", back_populates="examen")


class FormulaConsumo(Base):
    """
    Fórmula de consumo de reactivos/insumos por examen (Bill of Materials - BOM)
    """
    __tablename__ = "formulas_consumo"

    id = Column(Integer, primary_key=True, index=True)
    examen_id = Column(Integer, ForeignKey("examenes.id"), nullable=False)
    reactivo_id = Column(Integer, ForeignKey("reactivos.id"), nullable=False)
    cantidad_consumo = Column(Float, nullable=False)  # Cantidad consumida por examen

    # Relaciones
    examen = relationship("Examen", back_populates="formulas")
    reactivo = relationship("Reactivo", back_populates="formulas_examen")

    @property
    def reactivo_nombre(self) -> str:
        return self.reactivo.nombre if self.reactivo else ""
