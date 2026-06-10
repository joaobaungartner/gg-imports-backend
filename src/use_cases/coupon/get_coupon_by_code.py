from src.entities.coupon import CouponEntity
from src.repositories.coupon_repository import CouponRepository


class GetCouponByCodeUseCase:
    def __init__(self, coupon_repository: CouponRepository):
        self.coupon_repository = coupon_repository

    def execute(self, codigo: str) -> CouponEntity:
        codigo_normalizado = codigo.strip().upper()
        coupon = self.coupon_repository.get_by_code(codigo_normalizado)
        if not coupon:
            raise ValueError("Cupom não encontrado")
        return coupon
