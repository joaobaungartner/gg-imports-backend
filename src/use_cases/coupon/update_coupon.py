from datetime import date, datetime
from decimal import Decimal

from src.entities.coupon import CouponEntity
from src.repositories.coupon_repository import CouponRepository


class UpdateCouponUseCase:
    def __init__(self, coupon_repository: CouponRepository):
        self.coupon_repository = coupon_repository
        # TODO: validar permissão de Admin quando middleware existir

    def execute(
        self,
        coupon_id: int,
        codigo: str | None = None,
        desconto: float | None = None,
        validade: date | datetime | None = None,
        ativo: bool | None = None,
    ) -> CouponEntity:
        coupon = self.coupon_repository.get_by_id(coupon_id)
        if not coupon:
            raise ValueError("Cupom não encontrado")

        if codigo is not None:
            codigo_normalizado = codigo.strip().upper()
            if (
                codigo_normalizado != coupon.codigo
                and self.coupon_repository.code_exists(codigo_normalizado)
            ):
                raise ValueError("Código de cupom já cadastrado")

        desconto_decimal = Decimal(str(desconto)) if desconto is not None else None
        coupon.atualizar_cupom(
            codigo=codigo,
            desconto=desconto_decimal,
            validade=validade,
            ativo=ativo,
        )

        update_data = {}
        if codigo is not None:
            update_data["codigo"] = coupon.codigo
        if desconto is not None:
            update_data["desconto"] = coupon.desconto
        if validade is not None:
            update_data["validade"] = (
                validade.date() if isinstance(validade, datetime) else validade
            )
        if ativo is not None:
            update_data["ativo"] = coupon.ativo

        if not update_data:
            return coupon

        updated_coupon = self.coupon_repository.update(coupon_id, update_data)
        if not updated_coupon:
            raise ValueError("Cupom não encontrado")

        return updated_coupon
