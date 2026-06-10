from decimal import Decimal

from pydantic import BaseModel, Field


class OrderItemCreate(BaseModel):
    order_id: int = Field(..., gt=0)
    product_id: int = Field(..., gt=0)
    quantidade: int = Field(..., gt=0)


class OrderItemUpdate(BaseModel):
    quantidade: int | None = Field(default=None, gt=0)


class OrderItemResponse(BaseModel):
    id: int
    order_id: int
    product_id: int
    quantidade: int
    preco_unitario: Decimal
    subtotal: Decimal
    ativo: bool

    class Config:
        from_attributes = True


class OrderItemListResponse(BaseModel):
    id: int
    product_id: int
    quantidade: int
    preco_unitario: Decimal
    subtotal: Decimal
    ativo: bool

    class Config:
        from_attributes = True
