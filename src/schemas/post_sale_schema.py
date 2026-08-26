from datetime import datetime
from pydantic import BaseModel, Field


class PostSaleCreate(BaseModel):
    order_id: int = Field(..., gt=0)
    request_type: str = Field(..., pattern="^(RETURN|EXCHANGE|REFUND)$")
    reason: str = Field(..., min_length=5, max_length=2000)


class PostSaleUpdate(BaseModel):
    status: str = Field(..., pattern="^(REQUESTED|APPROVED|REJECTED|COMPLETED)$")
    admin_note: str | None = Field(default=None, max_length=2000)


class PostSaleResponse(BaseModel):
    id: int
    order_id: int
    client_id: int
    request_type: str
    reason: str
    status: str
    admin_note: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
