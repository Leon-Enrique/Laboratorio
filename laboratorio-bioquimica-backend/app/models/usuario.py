from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.db.session import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    nombre = Column(String, nullable=False)
    rol = Column(String, default="paciente")  # admin, bioquimico, paciente
    activo = Column(Boolean, default=True)

    # Relación con órdenes asignadas (para bioquímicos)
    ordenes_asignadas = relationship("Orden", back_populates="bioquimico")
    
    # Relación con el registro de paciente (opcional si el usuario es un paciente)
    paciente_rel = relationship("Paciente", back_populates="usuario", uselist=False)


class Paciente(Base):
    __tablename__ = "pacientes"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    dni = Column(String, unique=True, index=True, nullable=False)  # Cédula/DNI/RUT
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    genero = Column(String, nullable=False)  # M, F, Otro
    telefono = Column(String, nullable=True)
    direccion = Column(String, nullable=True)

    # Relaciones
    usuario = relationship("Usuario", back_populates="paciente_rel")
    ordenes = relationship("Orden", back_populates="paciente")
