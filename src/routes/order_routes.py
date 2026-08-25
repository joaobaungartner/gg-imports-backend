from decimal import Decimal

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.entities.user import UserEntity
from src.middlewares.auth import (
    ensure_order_owner_or_admin,
    get_current_admin,
    get_current_user,
    get_optional_user,
)
from src.repositories.address_repository import AddressRepository
from src.repositories.client_repository import ClientRepository
from src.repositories.coupon_repository import CouponRepository
from src.repositories.order_item_repository import OrderItemRepository
from src.repositories.order_repository import OrderRepository
from src.repositories.order_status_history_repository import (
    OrderStatusHistoryRepository,
)
from src.repositories.product_repository import ProductRepository
from src.routes.mappers import to_order_list_response, to_order_response
from src.routes.utils import run_use_case
from src.schemas.order_schema import (
    OrderCreate,
    OrderItemCreate,
    OrderListResponse,
    OrderResponse,
    OrderStatusUpdate,
    OrderTrackRequest,
)
from src.use_cases.order.get_my_orders import GetMyOrdersUseCase
from src.use_cases.order.track_order import TrackOrderUseCase
from src.use_cases.address.validate_address_for_order import (
    ValidateAddressForOrderUseCase,
)
from src.use_cases.order.add_order_item import AddOrderItemUseCase
from src.use_cases.order.apply_coupon_to_order import ApplyCouponToOrderUseCase
from src.use_cases.order.calculate_order_total import CalculateOrderTotalUseCase
from src.use_cases.order.cancel_order import CancelOrderUseCase
from src.use_cases.order.confirm_order import ConfirmOrderUseCase
from src.use_cases.order.create_checkout_order import CreateCheckoutOrderUseCase
from src.use_cases.order.get_order_by_id import GetOrderByIdUseCase
from src.use_cases.order.get_orders_by_client import GetOrdersByClientUseCase
from src.use_cases.order.list_orders import ListOrdersUseCase
from src.use_cases.order.remove_order_item import RemoveOrderItemUseCase
from src.use_cases.order.update_order_status import UpdateOrderStatusUseCase


class ApplyCouponToOrderRequest(BaseModel):
    cupom_id: int = Field(..., gt=0)


router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    def _execute():
        use_case = CreateCheckoutOrderUseCase(
            OrderRepository(db),
            ProductRepository(db),
            ClientRepository(db),
        )
        items = [
            {
                "product_id": item.product_id,
                "quantity": item.quantity,
            }
            for item in payload.items
        ]
        order = use_case.execute(
            customer_name=payload.customer_name,
            customer_email=payload.customer_email,
            customer_phone=payload.customer_phone,
            customer_cpf=payload.customer_cpf,
            shipping_address=payload.shipping_address.model_dump(),
            shipping_method=payload.shipping_method,
            payment_method=payload.payment_method,
            frete=payload.frete,
            items=items,
            authenticated_user_id=current_user.id,
        )
        history = OrderStatusHistoryRepository(db).list_by_order_id(order.id)
        return to_order_response(order, timeline=history)

    return run_use_case(_execute)


@router.get("/me", response_model=list[OrderListResponse])
def get_my_orders(
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    def _execute():
        use_case = GetMyOrdersUseCase(
            ClientRepository(db),
            OrderRepository(db),
        )
        orders = use_case.execute(current_user.id)
        return [to_order_list_response(order) for order in orders]

    return run_use_case(_execute)


@router.post("/track", response_model=OrderResponse)
def track_order(
    payload: OrderTrackRequest,
    db: Session = Depends(get_db),
):
    def _execute():
        use_case = TrackOrderUseCase(OrderRepository(db))
        order = use_case.execute(payload.order_id, payload.identifier)
        history = OrderStatusHistoryRepository(db).list_by_order_id(order.id)
        return to_order_response(order, timeline=history)

    return run_use_case(_execute)


@router.get("/", response_model=list[OrderListResponse])
def list_orders(
    status: str | None = Query(default=None),
    client_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = ListOrdersUseCase(OrderRepository(db))
        orders = use_case.execute(status=status, client_id=client_id)
        return [to_order_list_response(order) for order in orders]

    return run_use_case(_execute)


@router.get("/client/{client_id}", response_model=list[OrderListResponse])
def get_orders_by_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    from src.middlewares.auth import ensure_client_owner_or_admin

    ensure_client_owner_or_admin(client_id, current_user, db)

    def _execute():
        use_case = GetOrdersByClientUseCase(
            ClientRepository(db), OrderRepository(db)
        )
        orders = use_case.execute(client_id)
        return [to_order_list_response(order) for order in orders]

    return run_use_case(_execute)


@router.get("/{order_id}", response_model=OrderResponse)
def get_order_by_id(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity | None = Depends(get_optional_user),
):
    ensure_order_owner_or_admin(order_id, current_user, db, allow_public_guest=True)

    def _execute():
        use_case = GetOrderByIdUseCase(OrderRepository(db))
        order = use_case.execute(order_id)
        history = OrderStatusHistoryRepository(db).list_by_order_id(order_id)
        return to_order_response(order, timeline=history)

    return run_use_case(_execute)


@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = UpdateOrderStatusUseCase(
            OrderRepository(db),
            OrderStatusHistoryRepository(db),
            ProductRepository(db),
        )
        order = use_case.execute(
            order_id,
            payload.status,
            admin_id=current_user.id,
        )
        history = OrderStatusHistoryRepository(db).list_by_order_id(order_id)
        return to_order_response(order, timeline=history)

    return run_use_case(_execute)


@router.patch("/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_order_owner_or_admin(order_id, current_user, db)

    def _execute():
        use_case = CancelOrderUseCase(
            OrderRepository(db),
            OrderStatusHistoryRepository(db),
            ProductRepository(db),
        )
        order = use_case.execute(order_id, changed_by_user_id=current_user.id)
        history = OrderStatusHistoryRepository(db).list_by_order_id(order_id)
        return to_order_response(order, timeline=history)

    return run_use_case(_execute)


@router.get("/{order_id}/total", response_model=OrderResponse)
def calculate_order_total(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_order_owner_or_admin(order_id, current_user, db)

    def _execute():
        use_case = CalculateOrderTotalUseCase(OrderRepository(db))
        return to_order_response(use_case.execute(order_id))

    return run_use_case(_execute)


@router.post("/{order_id}/items", response_model=OrderResponse)
def add_order_item(
    order_id: int,
    payload: OrderItemCreate,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_order_owner_or_admin(order_id, current_user, db)

    def _execute():
        use_case = AddOrderItemUseCase(
            OrderRepository(db),
            OrderItemRepository(db),
            ProductRepository(db),
        )
        order = use_case.execute(order_id, payload.product_id, payload.quantidade)
        return to_order_response(order)

    return run_use_case(_execute)


@router.delete("/{order_id}/items/{order_item_id}", response_model=OrderResponse)
def remove_order_item(
    order_id: int,
    order_item_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_order_owner_or_admin(order_id, current_user, db)

    def _execute():
        use_case = RemoveOrderItemUseCase(OrderRepository(db))
        return to_order_response(use_case.execute(order_id, order_item_id))

    return run_use_case(_execute)


@router.post("/{order_id}/coupon", response_model=OrderResponse)
def apply_coupon_to_order(
    order_id: int,
    payload: ApplyCouponToOrderRequest,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_order_owner_or_admin(order_id, current_user, db)

    def _execute():
        use_case = ApplyCouponToOrderUseCase(
            OrderRepository(db), CouponRepository(db)
        )
        return to_order_response(use_case.execute(order_id, payload.cupom_id))

    return run_use_case(_execute)


@router.patch("/{order_id}/confirm", response_model=OrderResponse)
def confirm_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_order_owner_or_admin(order_id, current_user, db)

    def _execute():
        validate_address = ValidateAddressForOrderUseCase(AddressRepository(db))
        use_case = ConfirmOrderUseCase(
            ClientRepository(db),
            OrderRepository(db),
            validate_address,
        )
        return to_order_response(use_case.execute(order_id))

    return run_use_case(_execute)
