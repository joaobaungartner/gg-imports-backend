from src.entities.coupon import CouponEntity
from src.repositories.coupon_repository import CouponRepository


class GetCouponByIdUseCase:
    def __init__(self, coupon_repository: CouponRepository):
        self.coupon_repository = coupon_repository

    def execute(self, coupon_id: int) -> CouponEntity:
        coupon = self.coupon_repository.get_by_id(coupon_id)
        if not coupon:
            raise ValueError("Cupom não encontrado")
        return coupon
