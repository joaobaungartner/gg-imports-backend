from pydantic import BaseModel, Field


class CollectionProductItem(BaseModel):
    group_key: str
    selected: bool
    nome: str
    clube: str
    categoria: str
    tipo: str
    preco: str
    estoque_total: int
    imagem_url: str | None = None
    ativo: bool
    variant_ids: list[int]


class ProductCollectionResponse(BaseModel):
    slug: str
    name: str
    selected_count: int
    items: list[CollectionProductItem]


class ProductCollectionUpdate(BaseModel):
    group_keys: list[str] = Field(default_factory=list, max_length=500)


class HowToBuyStep(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    description: str = Field(..., min_length=1, max_length=1000)


class HowToBuyContent(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    subtitle: str = Field(..., min_length=1, max_length=500)
    eyebrow: str = Field(default="Passo a passo", min_length=1, max_length=80)
    steps: list[HowToBuyStep] = Field(..., min_length=1, max_length=20)
