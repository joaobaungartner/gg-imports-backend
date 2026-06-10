from src.entities.coupon import CouponEntity
from src.repositories.coupon_repository import CouponRepository


class ListCouponsUseCase:
    def __init__(self, coupon_repository: CouponRepository):
        self.coupon_repository = coupon_repository
        # TODO: validar permissão de Admin quando middleware existir

    def execute(
        self,
        ativo: bool | None = None,
        expirado: bool | None = None,
    ) -> list[CouponEntity]:
        if expirado is True:
            return self.coupon_repository.list_expired()

        if ativo is True:
            coupons = self.coupon_repository.list_active()
        elif ativo is False:
            coupons = [
                coupon
                for coupon in self.coupon_repository.list_all()
                if not coupon.ativo
            ]
        else:
            coupons = self.coupon_repository.list_all()

        if expirado is False:
            return [coupon for coupon in coupons if not coupon.esta_expirado()]

        return coupons
