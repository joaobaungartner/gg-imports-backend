from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.entities.user import UserEntity
from src.middlewares.auth import (
    ensure_order_owner_or_admin,
    ensure_payment_access_by_order,
    ensure_payment_owner_or_admin,
    get_current_admin,
    get_current_user,
)
from src.repositories.order_repository import OrderRepository
from src.repositories.payment_repository import PaymentRepository
from src.routes.mappers import to_payment_list_response, to_payment_response
from src.routes.utils import run_use_case
from src.schemas.payment_schema import (
    PaymentCreate,
    PaymentListResponse,
    PaymentResponse,
    PaymentStatusUpdate,
)
from src.use_cases.payment.cancel_payment import CancelPaymentUseCase
from src.use_cases.payment.confirm_payment import ConfirmPaymentUseCase
from src.use_cases.payment.create_payment import CreatePaymentUseCase
from src.use_cases.payment.get_payment_by_id import GetPaymentByIdUseCase
from src.use_cases.payment.get_payment_by_order import GetPaymentByOrderUseCase
from src.use_cases.payment.list_payments import ListPaymentsUseCase
from src.use_cases.payment.process_payment import ProcessPaymentUseCase
from src.use_cases.payment.refund_payment import RefundPaymentUseCase
from src.use_cases.payment.update_payment_status import UpdatePaymentStatusUseCase


class PaymentConfirmBody(BaseModel):
    codigo_transacao: str = Field(..., min_length=1)


router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_order_owner_or_admin(payload.order_id, current_user, db)

    def _execute():
        use_case = CreatePaymentUseCase(
            OrderRepository(db), PaymentRepository(db)
        )
        payment = use_case.execute(
            order_id=payload.order_id,
            metodo=payload.metodo,
            valor=payload.valor,
        )
        return to_payment_response(payment)

    return run_use_case(_execute)


@router.get("/", response_model=list[PaymentListResponse])
def list_payments(
    status: str | None = Query(default=None),
    metodo: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = ListPaymentsUseCase(PaymentRepository(db))
        payments = use_case.execute(status=status, metodo=metodo)
        return [to_payment_list_response(payment) for payment in payments]

    return run_use_case(_execute)


@router.get("/order/{order_id}", response_model=PaymentResponse)
def get_payment_by_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_payment_access_by_order(order_id, current_user, db)

    def _execute():
        use_case = GetPaymentByOrderUseCase(PaymentRepository(db))
        return to_payment_response(use_case.execute(order_id))

    return run_use_case(_execute)


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment_by_id(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = GetPaymentByIdUseCase(PaymentRepository(db))
        return to_payment_response(use_case.execute(payment_id))

    return run_use_case(_execute)


@router.post("/{payment_id}/process", response_model=PaymentResponse)
def process_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_payment_owner_or_admin(payment_id, current_user, db)

    # TODO: integrar gateway de pagamento real (Mercado Pago, Stripe, etc.)
    def _execute():
        use_case = ProcessPaymentUseCase(PaymentRepository(db))
        return to_payment_response(use_case.execute(payment_id))

    return run_use_case(_execute)


@router.post("/{payment_id}/confirm", response_model=PaymentResponse)
def confirm_payment(
    payment_id: int,
    payload: PaymentConfirmBody,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_payment_owner_or_admin(payment_id, current_user, db)

    def _execute():
        use_case = ConfirmPaymentUseCase(
            PaymentRepository(db), OrderRepository(db)
        )
        return to_payment_response(
            use_case.execute(payment_id, payload.codigo_transacao)
        )

    return run_use_case(_execute)


@router.post("/{payment_id}/cancel", response_model=PaymentResponse)
def cancel_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_payment_owner_or_admin(payment_id, current_user, db)

    def _execute():
        use_case = CancelPaymentUseCase(PaymentRepository(db))
        return to_payment_response(use_case.execute(payment_id))

    return run_use_case(_execute)


@router.post("/{payment_id}/refund", response_model=PaymentResponse)
def refund_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = RefundPaymentUseCase(PaymentRepository(db))
        return to_payment_response(use_case.execute(payment_id))

    return run_use_case(_execute)


@router.patch("/{payment_id}/status", response_model=PaymentResponse)
def update_payment_status(
    payment_id: int,
    payload: PaymentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = UpdatePaymentStatusUseCase(PaymentRepository(db))
        return to_payment_response(
            use_case.execute(payment_id, payload.status)
        )

    return run_use_case(_execute)
