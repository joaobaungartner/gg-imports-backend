from decimal import Decimal

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.repositories.order_item_repository import OrderItemRepository
from src.repositories.order_repository import OrderRepository
from src.repositories.product_repository import ProductRepository
from src.routes.mappers import to_order_item_list_response, to_order_item_response
from src.routes.utils import run_use_case
from src.schemas.order_item_schema import (
    OrderItemCreate,
    OrderItemListResponse,
    OrderItemResponse,
    OrderItemUpdate,
)
from src.use_cases.order_item.calculate_order_item_subtotal import (
    CalculateOrderItemSubtotalUseCase,
)
from src.use_cases.order_item.create_order_item import CreateOrderItemUseCase
from src.use_cases.order_item.get_order_item_by_id import GetOrderItemByIdUseCase
from src.use_cases.order_item.get_order_items_by_order import (
    GetOrderItemsByOrderUseCase,
)
from src.use_cases.order_item.remove_order_item import RemoveOrderItemUseCase
from src.use_cases.order_item.update_order_item_quantity import (
    UpdateOrderItemQuantityUseCase,
)


class OrderItemSubtotalResponse(BaseModel):
    id: int
    subtotal: Decimal


router = APIRouter(prefix="/order-items", tags=["Order Items"])


@router.post("/", response_model=OrderItemResponse, status_code=status.HTTP_201_CREATED)
def create_order_item(payload: OrderItemCreate, db: Session = Depends(get_db)):
    def _execute():
        use_case = CreateOrderItemUseCase(
            OrderRepository(db),
            OrderItemRepository(db),
            ProductRepository(db),
        )
        item = use_case.execute(
            payload.order_id, payload.product_id, payload.quantidade
        )
        return to_order_item_response(item)

    return run_use_case(_execute)


@router.get("/{order_item_id}", response_model=OrderItemResponse)
def get_order_item_by_id(order_item_id: int, db: Session = Depends(get_db)):
    def _execute():
        use_case = GetOrderItemByIdUseCase(OrderItemRepository(db))
        return to_order_item_response(use_case.execute(order_item_id))

    return run_use_case(_execute)


@router.get("/order/{order_id}", response_model=list[OrderItemListResponse])
def get_order_items_by_order(order_id: int, db: Session = Depends(get_db)):
    def _execute():
        use_case = GetOrderItemsByOrderUseCase(
            OrderRepository(db), OrderItemRepository(db)
        )
        items = use_case.execute(order_id)
        return [to_order_item_list_response(item) for item in items]

    return run_use_case(_execute)


@router.patch("/{order_item_id}/quantity", response_model=OrderItemResponse)
def update_order_item_quantity(
    order_item_id: int, payload: OrderItemUpdate, db: Session = Depends(get_db)
):
    def _execute():
        use_case = UpdateOrderItemQuantityUseCase(
            OrderRepository(db),
            OrderItemRepository(db),
            ProductRepository(db),
        )
        item = use_case.execute(order_item_id, payload.quantidade)
        return to_order_item_response(item)

    return run_use_case(_execute)


@router.get("/{order_item_id}/subtotal", response_model=OrderItemSubtotalResponse)
def calculate_order_item_subtotal(
    order_item_id: int, db: Session = Depends(get_db)
):
    def _execute():
        use_case = CalculateOrderItemSubtotalUseCase(OrderItemRepository(db))
        subtotal = use_case.execute(order_item_id)
        return OrderItemSubtotalResponse(id=order_item_id, subtotal=subtotal)

    return run_use_case(_execute)


@router.delete("/{order_item_id}", response_model=OrderItemResponse)
def remove_order_item(order_item_id: int, db: Session = Depends(get_db)):
    def _execute():
        use_case = RemoveOrderItemUseCase(
            OrderRepository(db), OrderItemRepository(db)
        )
        item = use_case.execute(order_item_id)
        return to_order_item_response(item)

    return run_use_case(_execute)
