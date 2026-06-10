from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CartCreate(BaseModel):
    client_id: int = Field(..., gt=0)


class CartItemCreate(BaseModel):
    product_id: int = Field(..., gt=0)
    quantidade: int = Field(..., gt=0)


class CartItemUpdate(BaseModel):
    quantidade: int = Field(..., gt=0)


class CartItemResponse(BaseModel):
    id: int
    cart_id: int
    product_id: int
    quantidade: int
    preco_unitario: Decimal
    subtotal: Decimal
    ativo: bool

    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    id: int
    client_id: int
    data_criacao: datetime
    ativo: bool
    itens: list[CartItemResponse]
    valor_total: Decimal

    class Config:
        from_attributes = True


class CartListResponse(BaseModel):
    id: int
    client_id: int
    data_criacao: datetime
    ativo: bool
    valor_total: Decimal

    class Config:
        from_attributes = True


class CartCheckoutResponse(BaseModel):
    cart_id: int
    client_id: int
    itens: list[CartItemResponse]
    valor_total: Decimal
    valido_para_checkout: bool

    class Config:
        from_attributes = True
