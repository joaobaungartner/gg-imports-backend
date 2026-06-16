from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.entities.user import UserEntity
from src.middlewares.auth import get_current_admin
from src.repositories.coupon_repository import CouponRepository
from src.routes.mappers import (
    to_coupon_apply_response,
    to_coupon_list_response,
    to_coupon_response,
)
from src.routes.utils import run_use_case
from src.schemas.coupon_schema import (
    CouponApply,
    CouponApplyResponse,
    CouponCreate,
    CouponListResponse,
    CouponResponse,
    CouponUpdate,
    CouponValidate,
)
from src.use_cases.coupon.activate_coupon import ActivateCouponUseCase
from src.use_cases.coupon.apply_coupon import ApplyCouponUseCase
from src.use_cases.coupon.create_coupon import CreateCouponUseCase
from src.use_cases.coupon.deactivate_coupon import DeactivateCouponUseCase
from src.use_cases.coupon.get_coupon_by_code import GetCouponByCodeUseCase
from src.use_cases.coupon.get_coupon_by_id import GetCouponByIdUseCase
from src.use_cases.coupon.list_coupons import ListCouponsUseCase
from src.use_cases.coupon.update_coupon import UpdateCouponUseCase
from src.use_cases.coupon.validate_coupon import ValidateCouponUseCase

router = APIRouter(prefix="/coupons", tags=["Coupons"])


@router.post("/", response_model=CouponResponse, status_code=status.HTTP_201_CREATED)
def create_coupon(
    payload: CouponCreate,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = CreateCouponUseCase(CouponRepository(db))
        coupon = use_case.execute(
            codigo=payload.codigo,
            desconto=payload.desconto,
            validade=payload.validade,
            ativo=payload.ativo if payload.ativo is not None else True,
        )
        return to_coupon_response(coupon)

    return run_use_case(_execute)


@router.get("/", response_model=list[CouponListResponse])
def list_coupons(
    active: bool | None = Query(default=None),
    expired: bool | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = ListCouponsUseCase(CouponRepository(db))
        coupons = use_case.execute(ativo=active, expirado=expired)
        return [to_coupon_list_response(coupon) for coupon in coupons]

    return run_use_case(_execute)


@router.post("/validate", response_model=CouponResponse)
def validate_coupon(payload: CouponValidate, db: Session = Depends(get_db)):
    def _execute():
        use_case = ValidateCouponUseCase(CouponRepository(db))
        return to_coupon_response(use_case.execute(payload.codigo))

    return run_use_case(_execute)


@router.post("/apply", response_model=CouponApplyResponse)
def apply_coupon(payload: CouponApply, db: Session = Depends(get_db)):
    def _execute():
        use_case = ApplyCouponUseCase(CouponRepository(db))
        result = use_case.execute(payload.codigo, payload.valor_total)
        return to_coupon_apply_response(result)

    return run_use_case(_execute)


@router.get("/code/{codigo}", response_model=CouponResponse)
def get_coupon_by_code(
    codigo: str,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = GetCouponByCodeUseCase(CouponRepository(db))
        return to_coupon_response(use_case.execute(codigo))

    return run_use_case(_execute)


@router.get("/{coupon_id}", response_model=CouponResponse)
def get_coupon_by_id(
    coupon_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = GetCouponByIdUseCase(CouponRepository(db))
        return to_coupon_response(use_case.execute(coupon_id))

    return run_use_case(_execute)


@router.put("/{coupon_id}", response_model=CouponResponse)
def update_coupon(
    coupon_id: int,
    payload: CouponUpdate,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = UpdateCouponUseCase(CouponRepository(db))
        coupon = use_case.execute(
            coupon_id=coupon_id,
            codigo=payload.codigo,
            desconto=payload.desconto,
            validade=payload.validade,
            ativo=payload.ativo,
        )
        return to_coupon_response(coupon)

    return run_use_case(_execute)


@router.patch("/{coupon_id}/activate", response_model=CouponResponse)
def activate_coupon(
    coupon_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = ActivateCouponUseCase(CouponRepository(db))
        return to_coupon_response(use_case.execute(coupon_id))

    return run_use_case(_execute)


@router.patch("/{coupon_id}/deactivate", response_model=CouponResponse)
def deactivate_coupon(
    coupon_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = DeactivateCouponUseCase(CouponRepository(db))
        return to_coupon_response(use_case.execute(coupon_id))

    return run_use_case(_execute)
