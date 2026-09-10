from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):
    order_id: int = Field(..., gt=0)
    metodo: str = Field(..., min_length=1)
    # Compatibilidade com clientes antigos; o valor informado nunca é utilizado.
    valor: float | None = Field(default=None, gt=0)


class PaymentProcess(BaseModel):
    token: str | None = Field(default=None, min_length=1)
    payment_method_id: str | None = Field(default=None, min_length=1)
    issuer_id: str | None = None
    installments: int | None = Field(default=None, ge=1, le=24)
    payer_email: str | None = None
    identification_type: str | None = None
    identification_number: str | None = None


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
    gateway: str | None = None
    gateway_status: str | None = None
    status_detail: str | None = None
    payment_method_id: str | None = None
    installments: int | None = None
    pix_qr_code: str | None = None
    pix_qr_code_base64: str | None = None
    pix_ticket_url: str | None = None
    expires_at: datetime | None = None
    refunded_amount: Decimal = Decimal("0")

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
