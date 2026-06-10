from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    nome: str = Field(..., min_length=1)
    descricao: str | None = None


class CategoryUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1)
    descricao: str | None = None
    ativo: bool | None = None


class CategoryResponse(BaseModel):
    id: int
    nome: str
    descricao: str | None
    ativo: bool

    class Config:
        from_attributes = True


class CategoryListResponse(BaseModel):
    id: int
    nome: str
    descricao: str | None
    ativo: bool

    class Config:
        from_attributes = True
