from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from src.database.database import Base


class OrderModel(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(
        Integer, ForeignKey("clients.id"), nullable=False, index=True
    )
    endereco_id = Column(
        Integer, ForeignKey("addresses.id"), nullable=False, index=True
    )
    # TODO: ForeignKey("payments.id") quando PaymentModel existir
    pagamento_id = Column(Integer, nullable=True, index=True)
    cupom_id = Column(
        Integer, ForeignKey("coupons.id"), nullable=True, index=True
    )
    data_pedido = Column(DateTime, default=datetime.utcnow, nullable=False)
    valor_total = Column(Numeric(10, 2), nullable=False, default=0)
    desconto_cupom = Column(Numeric(10, 2), nullable=False, default=0)
    status = Column(String(20), default="PENDING", nullable=False, index=True)
    ativo = Column(Boolean, default=True, nullable=False)

    client = relationship("ClientModel", backref="orders")
    endereco = relationship("AddressModel", backref="orders")
    cupom = relationship("CouponModel", back_populates="orders")
    itens = relationship(
        "OrderItemModel",
        back_populates="order",
        cascade="all, delete-orphan",
    )
