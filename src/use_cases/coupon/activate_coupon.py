from src.entities.coupon import CouponEntity
from src.repositories.coupon_repository import CouponRepository


class ActivateCouponUseCase:
    def __init__(self, coupon_repository: CouponRepository):
        self.coupon_repository = coupon_repository
        # TODO: validar permissão de Admin quando middleware existir

    def execute(self, coupon_id: int) -> CouponEntity:
        coupon = self.coupon_repository.get_by_id(coupon_id)
        if not coupon:
            raise ValueError("Cupom não encontrado")

        activated_coupon = self.coupon_repository.activate(coupon_id)
        if not activated_coupon:
            raise ValueError("Cupom não encontrado")

        return activated_coupon
