from datetime import date, datetime
from decimal import Decimal

from src.entities.coupon import CouponEntity
from src.repositories.coupon_repository import CouponRepository


class CreateCouponUseCase:
    def __init__(self, coupon_repository: CouponRepository):
        self.coupon_repository = coupon_repository
        # TODO: validar permissão de Admin quando middleware existir

    def execute(
        self,
        codigo: str,
        desconto: float,
        validade: date | datetime,
        ativo: bool = True,
    ) -> CouponEntity:
        codigo_normalizado = codigo.strip().upper()
        if self.coupon_repository.code_exists(codigo_normalizado):
            raise ValueError("Código de cupom já cadastrado")

        coupon = CouponEntity(
            id=None,
            codigo=codigo_normalizado,
            desconto=Decimal(str(desconto)),
            validade=validade,
            ativo=ativo,
        )

        return self.coupon_repository.create(coupon)
