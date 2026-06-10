from dataclasses import dataclass
from decimal import Decimal


@dataclass
class CartItemEntity:
    product_id: int
    quantidade: int
    preco_unitario: Decimal
    id: int | None = None
    cart_id: int | None = None
    ativo: bool = True

    def __post_init__(self) -> None:
        if isinstance(self.preco_unitario, (int, float)):
            self.preco_unitario = Decimal(str(self.preco_unitario))
        self.validar_item()

    def validar_item(self) -> None:
        if not self.product_id:
            raise ValueError("Produto não encontrado")
        if self.quantidade <= 0:
            raise ValueError("Quantidade inválida")
        if self.preco_unitario < 0:
            raise ValueError("Preço unitário inválido")

    def subtotal(self) -> Decimal:
        if not self.ativo:
            return Decimal("0")
        total = self.preco_unitario * self.quantidade
        if total < 0:
            return Decimal("0")
        return total

    def calcular_subtotal(self) -> Decimal:
        return self.subtotal()

    def atualizar_quantidade(self, quantidade: int) -> None:
        if quantidade <= 0:
            raise ValueError("Quantidade inválida")
        self.quantidade = quantidade

    def desativar(self) -> None:
        self.ativo = False
