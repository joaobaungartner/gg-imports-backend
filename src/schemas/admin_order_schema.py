from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from src.schemas.order_schema import OrderItemResponse


class AdminOrderStatusUpdate(BaseModel):
    status: str = Field(..., min_length=2, max_length=30)
    note: str | None = Field(default=None, max_length=1000)
    force: bool = False


class AdminOrderNotesUpdate(BaseModel):
    admin_notes: str | None = Field(default=None, max_length=2000)


class AdminOrderTrackingUpdate(BaseModel):
    codigo_rastreio: str = Field(..., min_length=3, max_length=100)
    url_rastreio: str | None = Field(default=None, max_length=500)


class OrderStatusHistoryResponse(BaseModel):
    id: int
    order_id: int
    previous_status: str | None = None
    new_status: str
    changed_by_user_id: int | None = None
    changed_by_name: str | None = None
    note: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class AdminOrderListItem(BaseModel):
    id: int
    data_pedido: datetime
    updated_at: datetime | None = None
    customer_name: str | None = None
    customer_email: str | None = None
    customer_phone: str | None = None
    item_count: int = 0
    valor_total: Decimal
    shipping_method: str | None = None
    payment_method: str | None = None
    payment_status: str | None = None
    status: str


class AdminOrderListResponse(BaseModel):
    items: list[AdminOrderListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class AdminOrderSummaryResponse(BaseModel):
    total: int
    pending_payment: int
    preparing: int
    shipped_or_ready: int
    delivered: int
    canceled: int


class AdminOrderDetailResponse(BaseModel):
    id: int
    client_id: int | None = None
    customer_name: str | None = None
    customer_email: str | None = None
    customer_phone: str | None = None
    customer_cpf: str | None = None
    shipping_cep: str | None = None
    shipping_street: str | None = None
    shipping_number: str | None = None
    shipping_complement: str | None = None
    shipping_neighborhood: str | None = None
    shipping_city: str | None = None
    shipping_state: str | None = None
    shipping_method: str | None = None
    payment_method: str | None = None
    payment_status: str | None = None
    pagamento_id: int | None = None
    cupom_id: int | None = None
    subtotal: Decimal
    frete: Decimal
    desconto_cupom: Decimal
    valor_total: Decimal
    data_pedido: datetime
    updated_at: datetime | None = None
    status: str
    ativo: bool
    admin_notes: str | None = None
    codigo_rastreio: str | None = None
    url_rastreio: str | None = None
    allowed_transitions: list[str] = []
    itens: list[OrderItemResponse]
    status_history: list[OrderStatusHistoryResponse] = []
