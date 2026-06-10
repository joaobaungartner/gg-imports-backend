from pydantic import BaseModel, Field


class AddressCreate(BaseModel):
    client_id: int = Field(..., gt=0)
    rua: str = Field(..., min_length=1)
    numero: str = Field(..., min_length=1)
    bairro: str = Field(..., min_length=1)
    cidade: str = Field(..., min_length=1)
    estado: str = Field(..., min_length=2, max_length=2)
    cep: str = Field(..., min_length=1)


class AddressUpdate(BaseModel):
    rua: str | None = Field(default=None, min_length=1)
    numero: str | None = Field(default=None, min_length=1)
    bairro: str | None = Field(default=None, min_length=1)
    cidade: str | None = Field(default=None, min_length=1)
    estado: str | None = Field(default=None, min_length=2, max_length=2)
    cep: str | None = Field(default=None, min_length=1)


class AddressResponse(BaseModel):
    id: int
    client_id: int
    rua: str
    numero: str
    bairro: str
    cidade: str
    estado: str
    cep: str
    ativo: bool

    class Config:
        from_attributes = True


class AddressListResponse(BaseModel):
    id: int
    rua: str
    numero: str
    bairro: str
    cidade: str
    estado: str
    cep: str
    ativo: bool

    class Config:
        from_attributes = True


class AddressForOrderResponse(BaseModel):
    id: int
    rua: str
    numero: str
    bairro: str
    cidade: str
    estado: str
    cep: str
    endereco_completo: str

    class Config:
        from_attributes = True
