from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.entities.order import OrderStatus
from src.entities.user import UserEntity
from src.middlewares.auth import get_current_admin, get_current_user
from src.repositories.client_repository import ClientRepository
from src.repositories.order_repository import OrderRepository
from src.repositories.post_sale_repository import PostSaleRepository
from src.schemas.post_sale_schema import PostSaleCreate, PostSaleResponse, PostSaleUpdate


router = APIRouter(prefix="/post-sales", tags=["Post Sales"])
admin_router = APIRouter(prefix="/admin/post-sales", tags=["Admin Post Sales"])


@router.post("/", response_model=PostSaleResponse, status_code=status.HTTP_201_CREATED)
def create_request(payload: PostSaleCreate, db: Session = Depends(get_db), current_user: UserEntity = Depends(get_current_user)):
    client = ClientRepository(db).get_by_user_id(current_user.id)
    order = OrderRepository(db).get_by_id(payload.order_id)
    if not client or not order or order.client_id != client.client_id:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if order.status not in (OrderStatus.DELIVERED, OrderStatus.PAID, OrderStatus.PREPARING):
        raise HTTPException(status_code=400, detail="Pedido não elegível para pós-venda")
    return PostSaleRepository(db).create(order.id, client.client_id, payload.request_type, payload.reason)


@router.get("/me", response_model=list[PostSaleResponse])
def my_requests(db: Session = Depends(get_db), current_user: UserEntity = Depends(get_current_user)):
    client = ClientRepository(db).get_by_user_id(current_user.id)
    return PostSaleRepository(db).list_for_client(client.client_id) if client else []


@admin_router.get("/", response_model=list[PostSaleResponse])
def list_requests(db: Session = Depends(get_db), current_user: UserEntity = Depends(get_current_admin)):
    return PostSaleRepository(db).list_all()


@admin_router.patch("/{request_id}", response_model=PostSaleResponse)
def update_request(request_id: int, payload: PostSaleUpdate, db: Session = Depends(get_db), current_user: UserEntity = Depends(get_current_admin)):
    updated = PostSaleRepository(db).update(request_id, payload.status, payload.admin_note)
    if not updated:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    return updated
