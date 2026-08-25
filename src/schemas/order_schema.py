from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


class ShippingAddressCreate(BaseModel):
    cep: str = Field(..., min_length=8, max_length=9)
    street: str = Field(..., min_length=1, max_length=255)
    number: str = Field(..., min_length=1, max_length=20)
    complement: str | None = Field(default=None, max_length=255)
    neighborhood: str = Field(..., min_length=1, max_length=100)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=2, max_length=2)


class CheckoutOrderItemCreate(BaseModel):
    product_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=255)
    image_url: str | None = None
    size: str = Field(..., min_length=1, max_length=20)
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)


class OrderCreate(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=255)
    customer_email: EmailStr
    customer_phone: str = Field(..., min_length=8, max_length=20)
    customer_cpf: str | None = Field(default=None, min_length=11, max_length=11)
    shipping_address: ShippingAddressCreate
    shipping_method: str = Field(default="ENTREGA", max_length=50)
    payment_method: str = Field(..., min_length=2, max_length=20)
    frete: Decimal = Field(default=Decimal("0"), ge=0)
    items: list[CheckoutOrderItemCreate] = Field(..., min_length=1)


class OrderItemCreate(BaseModel):
    product_id: int = Field(..., gt=0)
    quantidade: int = Field(..., gt=0)


class OrderUpdate(BaseModel):
    endereco_id: int | None = Field(default=None, gt=0)
    cupom_id: int | None = None


class OrderStatusUpdate(BaseModel):
    status: str


class OrderTrackRequest(BaseModel):
    order_id: int = Field(..., gt=0)
    identifier: str = Field(..., min_length=3, max_length=255)


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    nome_produto: str | None = None
    imagem_url: str | None = None
    tamanho: str | None = None
    quantidade: int
    preco_unitario: Decimal
    subtotal: Decimal
    ativo: bool = True

    class Config:
        from_attributes = True


class CustomerOrderTimelineItem(BaseModel):
    status: str
    label: str
    message: str
    created_at: datetime


class OrderResponse(BaseModel):
    id: int
    client_id: int | None = None
    endereco_id: int | None = None
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
    pagamento_id: int | None = None
    cupom_id: int | None = None
    subtotal: Decimal
    frete: Decimal
    data_pedido: datetime
    updated_at: datetime | None = None
    valor_total: Decimal
    status: str
    ativo: bool
    itens: list[OrderItemResponse]
    timeline: list[CustomerOrderTimelineItem] = []

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    id: int
    client_id: int | None = None
    customer_name: str | None = None
    data_pedido: datetime
    subtotal: Decimal
    frete: Decimal
    valor_total: Decimal
    status: str
    ativo: bool
    item_count: int = 0
    payment_method: str | None = None
    shipping_method: str | None = None

    class Config:
        from_attributes = True
