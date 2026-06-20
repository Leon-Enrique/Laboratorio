from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class Proveedor(Base):
    __tablename__ = "proveedores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True, nullable=False)
    telefono = Column(String, nullable=True)
    email = Column(String, nullable=True)
    direccion = Column(String, nullable=True)

    reactivos = relationship("Reactivo", back_populates="proveedor")
    lotes = relationship("Lote", back_populates="proveedor")


class Reactivo(Base):
    __tablename__ = "reactivos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True, nullable=False)
    stock_actual = Column(Float, default=0.0)
    stock_minimo = Column(Float, default=10.0)
    stock_de_seguridad = Column(Float, default=0.0)
    tiempo_entrega_proveedor_dias = Column(Integer, default=7)
    unidad_medida = Column(String, nullable=False)
    lote = Column(String, nullable=True)  # Lote activo (FEFO) — vista resumida
    fecha_vencimiento = Column(Date, nullable=True)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=True)

    proveedor = relationship("Proveedor", back_populates="reactivos")
    formulas_examen = relationship("FormulaConsumo", back_populates="reactivo")
    movimientos = relationship("MovimientoStock", back_populates="reactivo", cascade="all, delete-orphan")
    lotes = relationship("Lote", back_populates="reactivo", cascade="all, delete-orphan")
    mermas = relationship("MermaInventario", back_populates="reactivo", cascade="all, delete-orphan")
    ordenes_pedido = relationship("OrdenPedido", back_populates="reactivo", cascade="all, delete-orphan")


class Lote(Base):
    __tablename__ = "lotes"
    __table_args__ = (
        UniqueConstraint("reactivo_id", "codigo_lote", name="uq_reactivo_codigo_lote"),
    )

    id = Column(Integer, primary_key=True, index=True)
    reactivo_id = Column(Integer, ForeignKey("reactivos.id"), nullable=False, index=True)
    codigo_lote = Column(String, nullable=False)
    cantidad_disponible = Column(Float, default=0.0)
    fecha_vencimiento = Column(Date, nullable=False)
    fecha_ingreso = Column(Date, nullable=False)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=True)
    # ACTIVO | AGOTADO | VENCIDO | BLOQUEADO | Dado_de_Baja
    estado = Column(String, default="ACTIVO", nullable=False)

    reactivo = relationship("Reactivo", back_populates="lotes")
    proveedor = relationship("Proveedor", back_populates="lotes")
    movimientos = relationship("MovimientoStock", back_populates="lote")


class MovimientoStock(Base):
    __tablename__ = "movimientos_stock"

    id = Column(Integer, primary_key=True, index=True)
    reactivo_id = Column(Integer, ForeignKey("reactivos.id"), nullable=False, index=True)
    lote_id = Column(Integer, ForeignKey("lotes.id"), nullable=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    orden_id = Column(Integer, ForeignKey("ordenes.id"), nullable=True, index=True)
    cantidad = Column(Float, nullable=False)
    tipo = Column(String, nullable=False)  # ENTRADA, CONSUMO_AUTO, AJUSTE, BAJA_VENCIDO
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    descripcion = Column(String, nullable=True)
    stock_antes = Column(Float, nullable=True)
    stock_despues = Column(Float, nullable=True)
    stock_lote_antes = Column(Float, nullable=True)
    stock_lote_despues = Column(Float, nullable=True)

    reactivo = relationship("Reactivo", back_populates="movimientos")
    lote = relationship("Lote", back_populates="movimientos")
    usuario = relationship("Usuario", foreign_keys=[usuario_id])


class MermaInventario(Base):
    """Registro de pérdidas por baja de lote (soft delete)."""
    __tablename__ = "mermas_inventario"

    id = Column(Integer, primary_key=True, index=True)
    id_insumo = Column(Integer, ForeignKey("reactivos.id"), nullable=False, index=True)
    lote_id = Column(Integer, ForeignKey("lotes.id"), nullable=True, index=True)
    cantidad_perdida = Column(Float, nullable=False)
    fecha_baja = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    motivo = Column(String, nullable=False, default="Vencimiento")
    codigo_lote = Column(String, nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    reactivo = relationship("Reactivo", back_populates="mermas")
    lote = relationship("Lote")
    usuario = relationship("Usuario", foreign_keys=[usuario_id])


class OrdenPedido(Base):
    """Órdenes de compra a proveedores (MRP)."""
    __tablename__ = "ordenes_pedido"

    id = Column(Integer, primary_key=True, index=True)
    reactivo_id = Column(Integer, ForeignKey("reactivos.id"), nullable=False, index=True)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=True)
    cantidad_pedida = Column(Float, nullable=False)
    estado = Column(String, default="BORRADOR", nullable=False)  # BORRADOR | ENVIADA | RECIBIDA | CANCELADA
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_esperada = Column(Date, nullable=True)
    notas = Column(String, nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    reactivo = relationship("Reactivo", back_populates="ordenes_pedido")
    proveedor = relationship("Proveedor")
    usuario = relationship("Usuario", foreign_keys=[usuario_id])
