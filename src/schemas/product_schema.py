from decimal import Decimal

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    category_id: int = Field(..., gt=0)
    nome: str = Field(..., min_length=1)
    descricao: str | None = None
    preco: float = Field(..., gt=0)
    tamanho: str = Field(..., min_length=1)
    clube: str = Field(..., min_length=1)
    tipo: str = Field(..., min_length=1)
    estoque: int = Field(..., ge=0)
    imagem_url: str | None = None
    ativo: bool | None = True


class ProductUpdate(BaseModel):
    category_id: int | None = Field(default=None, gt=0)
    nome: str | None = Field(default=None, min_length=1)
    descricao: str | None = None
    preco: float | None = Field(default=None, gt=0)
    tamanho: str | None = Field(default=None, min_length=1)
    clube: str | None = Field(default=None, min_length=1)
    tipo: str | None = Field(default=None, min_length=1)
    estoque: int | None = Field(default=None, ge=0)
    imagem_url: str | None = None
    ativo: bool | None = None


class ProductStockUpdate(BaseModel):
    estoque: int = Field(..., ge=0)


class ProductStockChange(BaseModel):
    quantidade: int = Field(..., gt=0)


class ProductAvailabilityRequest(BaseModel):
    product_id: int = Field(..., gt=0)
    quantidade: int = Field(..., gt=0)


class ProductAvailabilityResponse(BaseModel):
    product_id: int
    disponivel: bool
    estoque_atual: int
    quantidade_solicitada: int

    class Config:
        from_attributes = True


class ProductResponse(BaseModel):
    id: int
    category_id: int
    nome: str
    descricao: str | None
    preco: Decimal
    tamanho: str
    clube: str
    tipo: str
    estoque: int
    imagem_url: str | None
    ativo: bool

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    id: int
    category_id: int
    nome: str
    preco: Decimal
    tamanho: str
    clube: str
    tipo: str
    estoque: int
    imagem_url: str | None
    ativo: bool

    class Config:
        from_attributes = True
