from decimal import Decimal

from pydantic import BaseModel, Field


class CartItemCreate(BaseModel):
    cart_id: int = Field(..., gt=0)
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


class CartItemListResponse(BaseModel):
    id: int
    product_id: int
    quantidade: int
    preco_unitario: Decimal
    subtotal: Decimal
    ativo: bool

    class Config:
        from_attributes = True


class CartItemSubtotalResponse(BaseModel):
    id: int
    subtotal: Decimal

    class Config:
        from_attributes = True
