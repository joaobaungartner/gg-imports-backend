from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from src.database.database import Base


class PaymentModel(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(
        Integer, ForeignKey("orders.id"), unique=True, nullable=False, index=True
    )
    metodo = Column(String(20), nullable=False)
    status = Column(String(20), default="PENDING", nullable=False, index=True)
    valor = Column(Numeric(10, 2), nullable=False)
    codigo_transacao = Column(String(100), nullable=True, unique=True, index=True)
    data_pagamento = Column(DateTime, nullable=True)
    ativo = Column(Boolean, default=True, nullable=False)

    order = relationship("OrderModel", back_populates="pagamento")
