from decimal import Decimal

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.entities.user import UserEntity
from src.middlewares.auth import (
    ensure_cart_item_owner_or_admin,
    ensure_cart_owner_or_admin,
    get_current_user,
)
from src.repositories.cart_item_repository import CartItemRepository
from src.repositories.cart_repository import CartRepository
from src.repositories.product_repository import ProductRepository
from src.routes.mappers import (
    to_cart_item_list_response,
    to_cart_item_response,
    to_cart_item_subtotal_response,
)
from src.routes.utils import run_use_case
from src.schemas.cart_item_schema import (
    CartItemCreate,
    CartItemListResponse,
    CartItemResponse,
    CartItemSubtotalResponse,
    CartItemUpdate,
)
from src.use_cases.cart_item.calculate_cart_item_subtotal import (
    CalculateCartItemSubtotalUseCase,
)
from src.use_cases.cart_item.create_cart_item import CreateCartItemUseCase
from src.use_cases.cart_item.get_cart_item_by_id import GetCartItemByIdUseCase
from src.use_cases.cart_item.get_cart_items_by_cart import GetCartItemsByCartUseCase
from src.use_cases.cart_item.reactivate_cart_item import ReactivateCartItemUseCase
from src.use_cases.cart_item.remove_cart_item import RemoveCartItemUseCase
from src.use_cases.cart_item.update_cart_item_quantity import (
    UpdateCartItemQuantityUseCase,
)


class ReactivateCartItemRequest(BaseModel):
    quantidade: int = Field(..., gt=0)


router = APIRouter(prefix="/cart-items", tags=["Cart Items"])


@router.post("/", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
def create_cart_item(
    payload: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_cart_owner_or_admin(payload.cart_id, current_user, db)

    def _execute():
        use_case = CreateCartItemUseCase(
            CartRepository(db),
            CartItemRepository(db),
            ProductRepository(db),
        )
        item = use_case.execute(
            payload.cart_id, payload.product_id, payload.quantidade
        )
        return to_cart_item_response(item)

    return run_use_case(_execute)


@router.get("/{cart_item_id}", response_model=CartItemResponse)
def get_cart_item_by_id(
    cart_item_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_cart_item_owner_or_admin(cart_item_id, current_user, db)

    def _execute():
        use_case = GetCartItemByIdUseCase(CartItemRepository(db))
        return to_cart_item_response(use_case.execute(cart_item_id))

    return run_use_case(_execute)


@router.get("/cart/{cart_id}", response_model=list[CartItemListResponse])
def get_cart_items_by_cart(
    cart_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_cart_owner_or_admin(cart_id, current_user, db)

    def _execute():
        use_case = GetCartItemsByCartUseCase(
            CartRepository(db), CartItemRepository(db)
        )
        items = use_case.execute(cart_id)
        return [to_cart_item_list_response(item) for item in items]

    return run_use_case(_execute)


@router.patch("/{cart_item_id}/quantity", response_model=CartItemResponse)
def update_cart_item_quantity(
    cart_item_id: int,
    payload: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_cart_item_owner_or_admin(cart_item_id, current_user, db)

    def _execute():
        use_case = UpdateCartItemQuantityUseCase(
            CartRepository(db),
            CartItemRepository(db),
            ProductRepository(db),
        )
        item = use_case.execute(cart_item_id, payload.quantidade)
        return to_cart_item_response(item)

    return run_use_case(_execute)


@router.get("/{cart_item_id}/subtotal", response_model=CartItemSubtotalResponse)
def calculate_cart_item_subtotal(
    cart_item_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_cart_item_owner_or_admin(cart_item_id, current_user, db)

    def _execute():
        use_case = CalculateCartItemSubtotalUseCase(CartItemRepository(db))
        subtotal = use_case.execute(cart_item_id)
        return to_cart_item_subtotal_response(cart_item_id, subtotal)

    return run_use_case(_execute)


@router.patch("/{cart_item_id}/reactivate", response_model=CartItemResponse)
def reactivate_cart_item(
    cart_item_id: int,
    payload: ReactivateCartItemRequest,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_cart_item_owner_or_admin(cart_item_id, current_user, db)

    def _execute():
        use_case = ReactivateCartItemUseCase(
            CartRepository(db), CartItemRepository(db)
        )
        item = use_case.execute(cart_item_id, payload.quantidade)
        return to_cart_item_response(item)

    return run_use_case(_execute)


@router.delete("/{cart_item_id}", response_model=CartItemResponse)
def remove_cart_item(
    cart_item_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_cart_item_owner_or_admin(cart_item_id, current_user, db)

    def _execute():
        use_case = RemoveCartItemUseCase(
            CartRepository(db), CartItemRepository(db)
        )
        item = use_case.execute(cart_item_id)
        return to_cart_item_response(item)

    return run_use_case(_execute)
