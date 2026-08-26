from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from src.database.database import Base


class OrderModel(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(
        Integer, ForeignKey("clients.id"), nullable=True, index=True
    )
    endereco_id = Column(
        Integer, ForeignKey("addresses.id"), nullable=True, index=True
    )
    customer_name = Column(String(255), nullable=True)
    customer_email = Column(String(255), nullable=True)
    customer_phone = Column(String(20), nullable=True)
    customer_cpf = Column(String(11), nullable=True)
    shipping_cep = Column(String(8), nullable=True)
    shipping_street = Column(String(255), nullable=True)
    shipping_number = Column(String(20), nullable=True)
    shipping_complement = Column(String(255), nullable=True)
    shipping_neighborhood = Column(String(100), nullable=True)
    shipping_city = Column(String(100), nullable=True)
    shipping_state = Column(String(2), nullable=True)
    shipping_method = Column(String(50), nullable=True)
    payment_method = Column(String(20), nullable=True)
    cupom_id = Column(
        Integer, ForeignKey("coupons.id"), nullable=True, index=True
    )
    data_pedido = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    admin_notes = Column(String(2000), nullable=True)
    subtotal = Column(Numeric(10, 2), nullable=False, default=0)
    frete = Column(Numeric(10, 2), nullable=False, default=0)
    valor_total = Column(Numeric(10, 2), nullable=False, default=0)
    desconto_cupom = Column(Numeric(10, 2), nullable=False, default=0)
    status = Column(String(30), default="PENDING_PAYMENT", nullable=False, index=True)
    estoque_reservado = Column(Boolean, default=False, nullable=False, index=True)
    reserva_expira_em = Column(DateTime, nullable=True, index=True)
    codigo_rastreio = Column(String(100), nullable=True)
    url_rastreio = Column(String(500), nullable=True)
    ativo = Column(Boolean, default=True, nullable=False)

    client = relationship("ClientModel", backref="orders")
    endereco = relationship("AddressModel", backref="orders")
    cupom = relationship("CouponModel", back_populates="orders")
    pagamento = relationship(
        "PaymentModel",
        back_populates="order",
        uselist=False,
        foreign_keys="PaymentModel.order_id",
        primaryjoin="OrderModel.id == PaymentModel.order_id",
    )
    itens = relationship(
        "OrderItemModel",
        back_populates="order",
        cascade="all, delete-orphan",
    )
    status_history = relationship(
        "OrderStatusHistoryModel",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderStatusHistoryModel.created_at.desc()",
    )
