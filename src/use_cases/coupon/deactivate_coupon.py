from src.entities.coupon import CouponEntity
from src.repositories.coupon_repository import CouponRepository


class DeactivateCouponUseCase:
    def __init__(self, coupon_repository: CouponRepository):
        self.coupon_repository = coupon_repository
        # TODO: validar permissão de Admin quando middleware existir

    def execute(self, coupon_id: int) -> CouponEntity:
        coupon = self.coupon_repository.get_by_id(coupon_id)
        if not coupon:
            raise ValueError("Cupom não encontrado")

        deactivated_coupon = self.coupon_repository.deactivate(coupon_id)
        if not deactivated_coupon:
            raise ValueError("Cupom não encontrado")

        return deactivated_coupon
