from dataclasses import dataclass
from decimal import Decimal

from src.use_cases.coupon.validate_coupon import ValidateCouponUseCase


@dataclass
class CouponApplyResult:
    coupon_id: int
    codigo: str
    valor_original: Decimal
    desconto_aplicado: Decimal
    valor_final: Decimal
    valido: bool


class ApplyCouponUseCase:
    def __init__(self, validate_coupon_use_case: ValidateCouponUseCase):
        self.validate_coupon_use_case = validate_coupon_use_case

    def execute(self, codigo: str, valor_total: float | Decimal) -> CouponApplyResult:
        valor_original = (
            Decimal(str(valor_total))
            if not isinstance(valor_total, Decimal)
            else valor_total
        )

        if valor_original < 0:
            raise ValueError("Valor total inválido")

        coupon = self.validate_coupon_use_case.execute(codigo)
        if coupon.id is None:
            raise ValueError("Cupom inválido")

        desconto_aplicado, valor_final = coupon.calcular_desconto(valor_original)

        return CouponApplyResult(
            coupon_id=coupon.id,
            codigo=coupon.codigo,
            valor_original=valor_original,
            desconto_aplicado=desconto_aplicado,
            valor_final=valor_final,
            valido=True,
        )
