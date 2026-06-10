from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from src.entities.cart_item import CartItemEntity


@dataclass
class CartEntity:
    id: int | None
    client_id: int
    data_criacao: datetime | None = None
    ativo: bool = True
    itens: list[CartItemEntity] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.validar_carrinho()

    def validar_carrinho(self) -> None:
        if not self.client_id:
            raise ValueError("Cliente não encontrado")

    def calcular_total(self) -> Decimal:
        total = sum(
            (item.subtotal() for item in self.itens if item.ativo),
            Decimal("0"),
        )
        if total < 0:
            return Decimal("0")
        return total

    def limpar_carrinho(self) -> None:
        for item in self.itens:
            if item.ativo:
                item.desativar()

    def adicionar_item(self, item: CartItemEntity) -> None:
        if not self.ativo:
            raise ValueError("Carrinho inativo")
        if item.quantidade <= 0:
            raise ValueError("Quantidade inválida")
        if not item.product_id:
            raise ValueError("Produto não encontrado")
        self.itens.append(item)

    def remover_item(self, item_id: int) -> None:
        item = self._buscar_item_por_id(item_id)
        if not item:
            raise ValueError("Item do carrinho não encontrado")
        item.desativar()

    def atualizar_quantidade_item(self, item_id: int, quantidade: int) -> None:
        item = self._buscar_item_por_id(item_id)
        if not item:
            raise ValueError("Item do carrinho não encontrado")
        item.atualizar_quantidade(quantidade)

    def buscar_item_por_produto(self, product_id: int) -> CartItemEntity | None:
        for item in self.itens:
            if item.product_id == product_id and item.ativo:
                return item
        return None

    def esta_vazio(self) -> bool:
        return not any(item.ativo for item in self.itens)

    def desativar(self) -> None:
        self.ativo = False
        self.limpar_carrinho()

    def _buscar_item_por_id(self, item_id: int) -> CartItemEntity | None:
        for item in self.itens:
            if item.id == item_id and item.ativo:
                return item
        return None
