from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):
    order_id: int = Field(..., gt=0)
    metodo: str = Field(..., min_length=1)
    valor: float = Field(..., gt=0)


class PaymentProcess(BaseModel):
    payment_id: int = Field(..., gt=0)


class PaymentConfirm(BaseModel):
    payment_id: int = Field(..., gt=0)
    codigo_transacao: str = Field(..., min_length=1)


class PaymentCancel(BaseModel):
    payment_id: int = Field(..., gt=0)


class PaymentRefund(BaseModel):
    payment_id: int = Field(..., gt=0)


class PaymentStatusUpdate(BaseModel):
    status: str


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    metodo: str
    status: str
    valor: Decimal
    codigo_transacao: str | None = None
    data_pagamento: datetime | None = None
    ativo: bool

    class Config:
        from_attributes = True


class PaymentListResponse(BaseModel):
    id: int
    order_id: int
    metodo: str
    status: str
    valor: Decimal
    data_pagamento: datetime | None = None
    ativo: bool

    class Config:
        from_attributes = True
