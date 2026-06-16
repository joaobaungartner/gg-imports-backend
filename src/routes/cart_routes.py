from decimal import Decimal

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.entities.user import UserEntity
from src.middlewares.auth import (
    ensure_cart_item_owner_or_admin,
    ensure_cart_owner_or_admin,
    ensure_client_owner_or_admin,
    get_current_user,
)
from src.repositories.cart_item_repository import CartItemRepository
from src.repositories.cart_repository import CartRepository
from src.repositories.client_repository import ClientRepository
from src.repositories.product_repository import ProductRepository
from src.routes.mappers import to_cart_checkout_response, to_cart_response
from src.routes.utils import run_use_case
from src.schemas.cart_schema import (
    CartCheckoutResponse,
    CartCreate,
    CartItemCreate,
    CartItemUpdate,
    CartResponse,
)
from src.use_cases.cart.add_item_to_cart import AddItemToCartUseCase
from src.use_cases.cart.calculate_cart_total import CalculateCartTotalUseCase
from src.use_cases.cart.clear_cart import ClearCartUseCase
from src.use_cases.cart.create_cart import CreateCartUseCase
from src.use_cases.cart.deactivate_cart import DeactivateCartUseCase
from src.use_cases.cart.get_cart_by_client import GetCartByClientUseCase
from src.use_cases.cart.get_cart_by_id import GetCartByIdUseCase
from src.use_cases.cart.prepare_cart_checkout import PrepareCartCheckoutUseCase
from src.use_cases.cart.remove_item_from_cart import RemoveItemFromCartUseCase
from src.use_cases.cart.update_cart_item_quantity import UpdateCartItemQuantityUseCase


class CartTotalResponse(BaseModel):
    total: Decimal


router = APIRouter(prefix="/carts", tags=["Carts"])


@router.post("/", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
def create_cart(
    payload: CartCreate,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_client_owner_or_admin(payload.client_id, current_user, db)

    def _execute():
        use_case = CreateCartUseCase(ClientRepository(db), CartRepository(db))
        cart = use_case.execute(payload.client_id)
        return to_cart_response(cart)

    return run_use_case(_execute)


@router.get("/{cart_id}", response_model=CartResponse)
def get_cart_by_id(
    cart_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_cart_owner_or_admin(cart_id, current_user, db)

    def _execute():
        use_case = GetCartByIdUseCase(CartRepository(db))
        return to_cart_response(use_case.execute(cart_id))

    return run_use_case(_execute)


@router.get("/client/{client_id}", response_model=CartResponse)
def get_cart_by_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_client_owner_or_admin(client_id, current_user, db)

    def _execute():
        use_case = GetCartByClientUseCase(
            ClientRepository(db), CartRepository(db)
        )
        return to_cart_response(use_case.execute(client_id))

    return run_use_case(_execute)


@router.post("/{cart_id}/items", response_model=CartResponse)
def add_item_to_cart(
    cart_id: int,
    payload: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_cart_owner_or_admin(cart_id, current_user, db)

    def _execute():
        use_case = AddItemToCartUseCase(
            CartRepository(db),
            CartItemRepository(db),
            ProductRepository(db),
        )
        cart = use_case.execute(cart_id, payload.product_id, payload.quantidade)
        return to_cart_response(cart)

    return run_use_case(_execute)


@router.patch("/items/{cart_item_id}", response_model=CartResponse)
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
        cart = use_case.execute(cart_item_id, payload.quantidade)
        return to_cart_response(cart)

    return run_use_case(_execute)


@router.delete("/items/{cart_item_id}", response_model=CartResponse)
def remove_item_from_cart(
    cart_item_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_cart_item_owner_or_admin(cart_item_id, current_user, db)

    def _execute():
        use_case = RemoveItemFromCartUseCase(
            CartRepository(db), CartItemRepository(db)
        )
        cart = use_case.execute(cart_item_id)
        return to_cart_response(cart)

    return run_use_case(_execute)


@router.delete("/{cart_id}/items", response_model=CartResponse)
def clear_cart(
    cart_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_cart_owner_or_admin(cart_id, current_user, db)

    def _execute():
        use_case = ClearCartUseCase(CartRepository(db))
        return to_cart_response(use_case.execute(cart_id))

    return run_use_case(_execute)


@router.get("/{cart_id}/total", response_model=CartTotalResponse)
def calculate_cart_total(
    cart_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_cart_owner_or_admin(cart_id, current_user, db)

    def _execute():
        use_case = CalculateCartTotalUseCase(CartRepository(db))
        total = use_case.execute(cart_id)
        return CartTotalResponse(total=total)

    return run_use_case(_execute)


@router.post("/{cart_id}/checkout/prepare", response_model=CartCheckoutResponse)
def prepare_cart_checkout(
    cart_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_cart_owner_or_admin(cart_id, current_user, db)

    # TODO: integrar CreateOrderUseCase no checkout completo
    def _execute():
        use_case = PrepareCartCheckoutUseCase(
            CartRepository(db), ProductRepository(db)
        )
        result = use_case.execute(cart_id)
        return to_cart_checkout_response(result)

    return run_use_case(_execute)


@router.patch("/{cart_id}/deactivate", response_model=CartResponse)
def deactivate_cart(
    cart_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_cart_owner_or_admin(cart_id, current_user, db)

    def _execute():
        use_case = DeactivateCartUseCase(CartRepository(db))
        return to_cart_response(use_case.execute(cart_id))

    return run_use_case(_execute)
