from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class OrderItemCreate(BaseModel):
    product_id: int = Field(..., gt=0)
    quantidade: int = Field(..., gt=0)


class OrderCreate(BaseModel):
    client_id: int = Field(..., gt=0)
    endereco_id: int = Field(..., gt=0)
    itens: list[OrderItemCreate] = Field(..., min_length=1)
    cupom_id: int | None = None


class OrderUpdate(BaseModel):
    endereco_id: int | None = Field(default=None, gt=0)
    cupom_id: int | None = None


class OrderStatusUpdate(BaseModel):
    status: str


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantidade: int
    preco_unitario: Decimal
    subtotal: Decimal
    ativo: bool = True

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    client_id: int
    endereco_id: int
    pagamento_id: int | None = None
    cupom_id: int | None = None
    data_pedido: datetime
    valor_total: Decimal
    status: str
    ativo: bool
    itens: list[OrderItemResponse]

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    id: int
    client_id: int
    data_pedido: datetime
    valor_total: Decimal
    status: str
    ativo: bool

    class Config:
        from_attributes = True
