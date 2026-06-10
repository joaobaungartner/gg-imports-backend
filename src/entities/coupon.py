from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass
class CouponEntity:
    id: int | None
    codigo: str
    desconto: Decimal
    validade: date | datetime
    ativo: bool = True

    def __post_init__(self) -> None:
        self.codigo = self.codigo.strip().upper()
        if isinstance(self.desconto, (int, float)):
            self.desconto = Decimal(str(self.desconto))
        self._validate_fields()

    def _validate_fields(self) -> None:
        if not self.codigo:
            raise ValueError("Código de cupom é obrigatório")
        if self.desconto <= 0:
            raise ValueError("Desconto inválido")
        if self.desconto > 100:
            raise ValueError("Desconto inválido")
        if not self.validade:
            raise ValueError("Validade inválida")

    def _validade_date(self) -> date:
        if isinstance(self.validade, datetime):
            return self.validade.date()
        return self.validade

    def esta_expirado(self) -> bool:
        return self._validade_date() < date.today()

    def esta_valido(self) -> bool:
        return self.ativo and not self.esta_expirado()

    def validar_cupom(self) -> None:
        if not self.codigo:
            raise ValueError("Código de cupom é obrigatório")
        if self.desconto <= 0 or self.desconto > 100:
            raise ValueError("Desconto inválido")
        if not self.validade:
            raise ValueError("Validade inválida")
        if not self.ativo:
            raise ValueError("Cupom inativo")
        if self.esta_expirado():
            raise ValueError("Cupom expirado")

    def ativar(self) -> None:
        self.ativo = True

    def desativar(self) -> None:
        self.ativo = False

    def atualizar_cupom(
        self,
        codigo: str | None = None,
        desconto: Decimal | None = None,
        validade: date | datetime | None = None,
        ativo: bool | None = None,
    ) -> None:
        if codigo is not None:
            self.codigo = codigo.strip().upper()
        if desconto is not None:
            self.desconto = (
                Decimal(str(desconto))
                if not isinstance(desconto, Decimal)
                else desconto
            )
        if validade is not None:
            self.validade = validade
        if ativo is not None:
            self.ativo = ativo
        self._validate_fields()

    def calcular_desconto(self, valor_total: Decimal) -> tuple[Decimal, Decimal]:
        if valor_total < 0:
            raise ValueError("Valor total inválido")
        self.validar_cupom()

        desconto_aplicado = (
            valor_total * self.desconto / Decimal("100")
        ).quantize(Decimal("0.01"))
        valor_final = valor_total - desconto_aplicado
        if valor_final < 0:
            valor_final = Decimal("0")
            desconto_aplicado = valor_total

        return desconto_aplicado, valor_final

    def aplicar_desconto(self, valor_total: Decimal) -> Decimal:
        _, valor_final = self.calcular_desconto(valor_total)
        return valor_final
