from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class CouponCreate(BaseModel):
    codigo: str = Field(..., min_length=1)
    desconto: float = Field(..., gt=0, le=100)
    validade: date
    ativo: bool | None = True


class CouponUpdate(BaseModel):
    codigo: str | None = Field(default=None, min_length=1)
    desconto: float | None = Field(default=None, gt=0, le=100)
    validade: date | None = None
    ativo: bool | None = None


class CouponResponse(BaseModel):
    id: int
    codigo: str
    desconto: Decimal
    validade: date
    ativo: bool

    class Config:
        from_attributes = True


class CouponValidate(BaseModel):
    codigo: str = Field(..., min_length=1)


class CouponApply(BaseModel):
    codigo: str = Field(..., min_length=1)
    valor_total: float = Field(..., ge=0)


class CouponApplyResponse(BaseModel):
    coupon_id: int
    codigo: str
    valor_original: Decimal
    desconto_aplicado: Decimal
    valor_final: Decimal
    valido: bool


class CouponListResponse(BaseModel):
    id: int
    codigo: str
    desconto: Decimal
    validade: date
    ativo: bool

    class Config:
        from_attributes = True
