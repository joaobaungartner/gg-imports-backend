from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
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
    gateway = Column(String(30), nullable=True)
    idempotency_key = Column(String(64), nullable=True, unique=True, index=True)
    gateway_status = Column(String(40), nullable=True)
    status_detail = Column(String(100), nullable=True)
    payment_method_id = Column(String(50), nullable=True)
    installments = Column(Integer, nullable=True)
    pix_qr_code = Column(Text, nullable=True)
    pix_qr_code_base64 = Column(Text, nullable=True)
    pix_ticket_url = Column(String(1000), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    refunded_amount = Column(Numeric(10, 2), nullable=False, default=0)
    last_reconciled_at = Column(DateTime, nullable=True)
    ativo = Column(Boolean, default=True, nullable=False)

    order = relationship(
        "OrderModel",
        back_populates="pagamento",
        foreign_keys=[order_id],
    )
