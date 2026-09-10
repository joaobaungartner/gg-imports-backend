from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.config.config import get_settings
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
from src.schemas.payment_schema import PaymentCreate, PaymentListResponse, PaymentProcess, PaymentResponse, PaymentStatusUpdate
from src.services.mercado_pago import MercadoPagoGateway, verify_webhook_signature
from src.use_cases.payment.cancel_payment import CancelPaymentUseCase
from src.use_cases.payment.create_payment import CreatePaymentUseCase
from src.use_cases.payment.get_payment_by_id import GetPaymentByIdUseCase
from src.use_cases.payment.get_payment_by_order import GetPaymentByOrderUseCase
from src.use_cases.payment.list_payments import ListPaymentsUseCase
from src.use_cases.payment.process_payment import ProcessPaymentUseCase
from src.use_cases.payment.reconcile_payment import ReconcilePaymentUseCase
from src.use_cases.payment.refund_payment import RefundPaymentUseCase
from src.use_cases.payment.update_payment_status import UpdatePaymentStatusUseCase


class PaymentConfirmBody(BaseModel):
    codigo_transacao: str = Field(..., min_length=1)


router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db), current_user: UserEntity = Depends(get_current_user)):
    ensure_order_owner_or_admin(payload.order_id, current_user, db)
    return run_use_case(lambda: to_payment_response(CreatePaymentUseCase(OrderRepository(db), PaymentRepository(db)).execute(payload.order_id, payload.metodo)))


@router.get("/", response_model=list[PaymentListResponse])
def list_payments(status_filter: str | None = Query(default=None, alias="status"), metodo: str | None = Query(default=None), db: Session = Depends(get_db), current_user: UserEntity = Depends(get_current_admin)):
    def execute():
        payments = ListPaymentsUseCase(PaymentRepository(db)).execute(status=status_filter, metodo=metodo)
        return [to_payment_list_response(payment) for payment in payments]
    return run_use_case(execute)


@router.get("/order/{order_id}", response_model=PaymentResponse)
def get_payment_by_order(order_id: int, db: Session = Depends(get_db), current_user: UserEntity = Depends(get_current_user)):
    ensure_payment_access_by_order(order_id, current_user, db)
    return run_use_case(lambda: to_payment_response(GetPaymentByOrderUseCase(PaymentRepository(db)).execute(order_id)))


@router.post("/webhooks/mercado-pago", status_code=status.HTTP_200_OK)
async def mercado_pago_webhook(request: Request, x_signature: str | None = Header(default=None), x_request_id: str | None = Header(default=None), db: Session = Depends(get_db)):
    settings = get_settings()
    data_id = request.query_params.get("data.id")
    if not data_id:
        body = await request.json()
        data_id = str((body.get("data") or {}).get("id") or "")
    if not verify_webhook_signature(secret=settings.MERCADO_PAGO_WEBHOOK_SECRET or "", signature=x_signature, request_id=x_request_id, data_id=data_id):
        raise HTTPException(status_code=401, detail="Assinatura do webhook inválida")
    if not settings.MERCADO_PAGO_ACCESS_TOKEN:
        raise HTTPException(status_code=503, detail="Mercado Pago não configurado")
    gateway = MercadoPagoGateway(settings.MERCADO_PAGO_ACCESS_TOKEN, settings.MERCADO_PAGO_API_BASE_URL)
    try:
        ReconcilePaymentUseCase(PaymentRepository(db), OrderRepository(db)).execute(gateway.get_payment(data_id))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"received": True}


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment_by_id(payment_id: int, db: Session = Depends(get_db), current_user: UserEntity = Depends(get_current_admin)):
    return run_use_case(lambda: to_payment_response(GetPaymentByIdUseCase(PaymentRepository(db)).execute(payment_id)))


@router.post("/{payment_id}/process", response_model=PaymentResponse)
def process_payment(payment_id: int, payload: PaymentProcess | None = None, db: Session = Depends(get_db), current_user: UserEntity = Depends(get_current_user)):
    ensure_payment_owner_or_admin(payment_id, current_user, db)
    card_data = payload.model_dump(exclude_none=True) if payload else None
    return run_use_case(lambda: to_payment_response(ProcessPaymentUseCase(PaymentRepository(db), OrderRepository(db)).execute(payment_id, card_data)))


@router.post("/{payment_id}/cancel", response_model=PaymentResponse)
def cancel_payment(payment_id: int, db: Session = Depends(get_db), current_user: UserEntity = Depends(get_current_user)):
    ensure_payment_owner_or_admin(payment_id, current_user, db)
    return run_use_case(lambda: to_payment_response(CancelPaymentUseCase(PaymentRepository(db)).execute(payment_id)))


@router.post("/{payment_id}/refund", response_model=PaymentResponse)
def refund_payment(payment_id: int, db: Session = Depends(get_db), current_user: UserEntity = Depends(get_current_admin)):
    return run_use_case(lambda: to_payment_response(RefundPaymentUseCase(PaymentRepository(db), OrderRepository(db)).execute(payment_id)))


@router.post("/{payment_id}/reconcile", response_model=PaymentResponse)
def reconcile_payment(payment_id: int, db: Session = Depends(get_db), current_user: UserEntity = Depends(get_current_admin)):
    def execute():
        payment = PaymentRepository(db).get_by_id(payment_id)
        if not payment or not payment.codigo_transacao:
            raise ValueError("Pagamento ainda não enviado ao Mercado Pago")
        settings = get_settings()
        if not settings.MERCADO_PAGO_ACCESS_TOKEN:
            raise ValueError("Mercado Pago não configurado")
        gateway = MercadoPagoGateway(settings.MERCADO_PAGO_ACCESS_TOKEN, settings.MERCADO_PAGO_API_BASE_URL)
        return to_payment_response(ReconcilePaymentUseCase(PaymentRepository(db), OrderRepository(db)).execute(gateway.get_payment(payment.codigo_transacao)))
    return run_use_case(execute)


@router.patch("/{payment_id}/status", response_model=PaymentResponse)
def update_payment_status(payment_id: int, payload: PaymentStatusUpdate, db: Session = Depends(get_db), current_user: UserEntity = Depends(get_current_admin)):
    return run_use_case(lambda: to_payment_response(UpdatePaymentStatusUseCase(PaymentRepository(db)).execute(payment_id, payload.status)))
