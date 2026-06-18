from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class Orden(Base):
    __tablename__ = "ordenes"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    codigo_orden = Column(String, unique=True, index=True, nullable=False)  # Código único de paciente
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_completado = Column(DateTime(timezone=True), nullable=True)
    estado = Column(String, default="PENDIENTE")  # PENDIENTE, PROCESANDO, COMPLETADO
    estado_pago = Column(String, default="PENDIENTE")  # PENDIENTE, PAGADO
    metodo_pago = Column(String, nullable=True)  # EFECTIVO, TRANSFERENCIA, TARJETA, QR
    fecha_pago = Column(DateTime(timezone=True), nullable=True)
    medico_solicitante = Column(String, nullable=True)
    prioridad = Column(String, default="NORMAL")  # NORMAL | URGENTE
    notas = Column(String, nullable=True)
    requiere_factura = Column(Boolean, default=False)
    nit_factura = Column(String, nullable=True)
    razon_social_factura = Column(String, nullable=True)
    bioquimico_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    # Relaciones
    paciente = relationship("Paciente", back_populates="ordenes")
    bioquimico = relationship("Usuario", back_populates="ordenes_asignadas")
    resultados = relationship("Resultado", back_populates="orden", cascade="all, delete-orphan")

    @property
    def precio_total(self) -> float:
        return sum(res.examen.precio_bob for res in self.resultados if res.examen)


class Resultado(Base):
    __tablename__ = "resultados"

    id = Column(Integer, primary_key=True, index=True)
    orden_id = Column(Integer, ForeignKey("ordenes.id"), nullable=False)
    examen_id = Column(Integer, ForeignKey("examenes.id"), nullable=False)
    valor_resultado = Column(JSON, nullable=True)  # Resultados en formato JSON {"Glucosa": "95", "Urea": "20"}
    pdf_url = Column(String, nullable=True)  # URL de Cloudinary o servidor local para el PDF firmado
    fecha_registro = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relaciones
    orden = relationship("Orden", back_populates="resultados")
    examen = relationship("Examen", back_populates="resultados")
