from dataclasses import dataclass
from decimal import Decimal


@dataclass
class ProductEntity:
    id: int | None
    category_id: int
    nome: str
    preco: Decimal
    tamanho: str
    clube: str
    tipo: str
    descricao: str | None = None
    estoque: int = 0
    imagem_url: str | None = None
    ativo: bool = True

    def __post_init__(self) -> None:
        if isinstance(self.preco, (int, float)):
            self.preco = Decimal(str(self.preco))
        self.nome = self.nome.strip()
        self.tamanho = self.tamanho.strip()
        self.clube = self.clube.strip()
        self.tipo = self.tipo.strip()
        if self.descricao is not None:
            self.descricao = self.descricao.strip() or None
        if self.imagem_url is not None:
            self.imagem_url = self.imagem_url.strip() or None
        self.validar_produto()

    def validar_produto(self) -> None:
        if not self.nome:
            raise ValueError("Nome do produto é obrigatório")
        if not self.category_id:
            raise ValueError("Categoria não encontrada")
        if self.preco <= 0:
            raise ValueError("Preço inválido")
        if not self.tamanho:
            raise ValueError("Tamanho inválido")
        if not self.clube:
            raise ValueError("Clube é obrigatório")
        if not self.tipo:
            raise ValueError("Tipo é obrigatório")
        if self.estoque < 0:
            raise ValueError("Estoque inválido")

    def atualizar_produto(
        self,
        category_id: int | None = None,
        nome: str | None = None,
        descricao: str | None = None,
        preco: Decimal | None = None,
        tamanho: str | None = None,
        clube: str | None = None,
        tipo: str | None = None,
        estoque: int | None = None,
        imagem_url: str | None = None,
        ativo: bool | None = None,
    ) -> None:
        if category_id is not None:
            self.category_id = category_id
        if nome is not None:
            self.nome = nome.strip()
        if descricao is not None:
            self.descricao = descricao.strip() or None
        if preco is not None:
            self.preco = (
                Decimal(str(preco)) if not isinstance(preco, Decimal) else preco
            )
        if tamanho is not None:
            self.tamanho = tamanho.strip()
        if clube is not None:
            self.clube = clube.strip()
        if tipo is not None:
            self.tipo = tipo.strip()
        if estoque is not None:
            self.atualizar_estoque(estoque)
        if imagem_url is not None:
            self.imagem_url = imagem_url.strip() or None
        if ativo is not None:
            self.ativo = ativo
        self.validar_produto()

    def atualizar_estoque(self, estoque: int) -> None:
        if estoque < 0:
            raise ValueError("Estoque inválido")
        self.estoque = estoque

    def aumentar_estoque(self, quantidade: int) -> None:
        if quantidade < 0:
            raise ValueError("Estoque inválido")
        self.estoque += quantidade

    def reduzir_estoque(self, quantidade: int) -> None:
        if quantidade < 0:
            raise ValueError("Estoque inválido")
        if quantidade > self.estoque:
            raise ValueError("Estoque insuficiente")
        self.estoque -= quantidade

    def verificar_estoque_disponivel(self, quantidade: int) -> bool:
        if quantidade <= 0:
            return False
        return self.estoque >= quantidade

    def esta_disponivel(self) -> bool:
        return self.ativo and self.estoque > 0

    def ativar(self) -> None:
        self.ativo = True

    def desativar(self) -> None:
        self.ativo = False
