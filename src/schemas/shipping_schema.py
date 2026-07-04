from decimal import Decimal

from pydantic import BaseModel, Field


class ShippingQuoteRequest(BaseModel):
    cep: str = Field(..., min_length=8, max_length=9)
    shipping_method: str = Field(..., max_length=50)
    item_count: int = Field(..., gt=0)


class ShippingQuoteResponse(BaseModel):
    shipping_method: str
    frete: Decimal
    label: str
