from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.entities.user import UserEntity
from src.middlewares.auth import get_current_admin
from src.repositories.order_repository import OrderRepository
from src.repositories.order_status_history_repository import (
    OrderStatusHistoryRepository,
)
from src.routes.mappers import (
    to_admin_order_detail_response,
    to_admin_order_list_item,
    to_order_status_history_response,
)
from src.routes.utils import run_use_case
from src.schemas.admin_order_schema import (
    AdminOrderDetailResponse,
    AdminOrderListResponse,
    AdminOrderNotesUpdate,
    AdminOrderStatusUpdate,
    AdminOrderSummaryResponse,
    OrderStatusHistoryResponse,
)
from src.use_cases.order.get_admin_order_by_id import GetAdminOrderByIdUseCase
from src.use_cases.order.get_admin_orders_summary import GetAdminOrdersSummaryUseCase
from src.use_cases.order.get_order_status_history import GetOrderStatusHistoryUseCase
from src.use_cases.order.list_admin_orders import ListAdminOrdersUseCase
from src.use_cases.order.update_admin_order_notes import UpdateAdminOrderNotesUseCase
from src.use_cases.order.update_admin_order_status import UpdateAdminOrderStatusUseCase

router = APIRouter(prefix="/admin/orders", tags=["Admin Orders"])


@router.get("/summary", response_model=AdminOrderSummaryResponse)
def get_orders_summary(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = GetAdminOrdersSummaryUseCase(OrderRepository(db))
        return use_case.execute(date_from=date_from, date_to=date_to)

    return run_use_case(_execute)


@router.get("/", response_model=AdminOrderListResponse)
def list_admin_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None),
    shipping_method: str | None = Query(default=None),
    payment_status: str | None = Query(default=None),
    payment_method: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    search: str | None = Query(default=None),
    sort: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = ListAdminOrdersUseCase(OrderRepository(db))
        result = use_case.execute(
            page=page,
            page_size=page_size,
            status=status,
            shipping_method=shipping_method,
            payment_status=payment_status,
            payment_method=payment_method,
            date_from=date_from,
            date_to=date_to,
            search=search,
            sort=sort,
        )
        items = [
            to_admin_order_list_item(row["order"], row["payment_status"])
            for row in result["items"]
        ]
        return AdminOrderListResponse(
            items=items,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"],
        )

    return run_use_case(_execute)


@router.get("/{order_id}", response_model=AdminOrderDetailResponse)
def get_admin_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = GetAdminOrderByIdUseCase(
            OrderRepository(db),
            OrderStatusHistoryRepository(db),
        )
        order, history, payment_status = use_case.execute(order_id)
        return to_admin_order_detail_response(order, history, payment_status)

    return run_use_case(_execute)


@router.patch("/{order_id}/status", response_model=AdminOrderDetailResponse)
def update_admin_order_status(
    order_id: int,
    payload: AdminOrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = UpdateAdminOrderStatusUseCase(
            OrderRepository(db),
            OrderStatusHistoryRepository(db),
        )
        use_case.execute(
            order_id=order_id,
            novo_status=payload.status,
            admin_user_id=current_user.id,
            note=payload.note,
            force=payload.force,
        )
        detail_use_case = GetAdminOrderByIdUseCase(
            OrderRepository(db),
            OrderStatusHistoryRepository(db),
        )
        order, history, payment_status = detail_use_case.execute(order_id)
        return to_admin_order_detail_response(order, history, payment_status)

    return run_use_case(_execute)


@router.patch("/{order_id}/notes", response_model=AdminOrderDetailResponse)
def update_admin_order_notes(
    order_id: int,
    payload: AdminOrderNotesUpdate,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        notes_use_case = UpdateAdminOrderNotesUseCase(OrderRepository(db))
        notes_use_case.execute(order_id, payload.admin_notes)
        detail_use_case = GetAdminOrderByIdUseCase(
            OrderRepository(db),
            OrderStatusHistoryRepository(db),
        )
        order, history, payment_status = detail_use_case.execute(order_id)
        return to_admin_order_detail_response(order, history, payment_status)

    return run_use_case(_execute)


@router.get("/{order_id}/history", response_model=list[OrderStatusHistoryResponse])
def get_admin_order_history(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        order = OrderRepository(db).get_by_id(order_id)
        if not order:
            raise ValueError("Pedido não encontrado")
        use_case = GetOrderStatusHistoryUseCase(OrderStatusHistoryRepository(db))
        history = use_case.execute(order_id)
        return [to_order_status_history_response(item) for item in history]

    return run_use_case(_execute)
