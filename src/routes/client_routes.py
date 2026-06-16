from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.entities.user import UserEntity
from src.middlewares.auth import (
    ensure_client_access_by_cpf,
    ensure_client_access_by_user_id,
    ensure_client_owner_or_admin,
    get_current_user,
)
from src.repositories.cart_item_repository import CartItemRepository
from src.repositories.cart_repository import CartRepository
from src.repositories.client_repository import ClientRepository
from src.repositories.product_repository import ProductRepository
from src.repositories.user_repository import UserRepository
from src.routes.mappers import to_cart_response, to_client_response, to_order_list_response
from src.routes.utils import run_use_case
from src.schemas.client_schema import ClientCartAdd, ClientCreate, ClientResponse, ClientUpdate
from src.schemas.order_schema import OrderListResponse
from src.schemas.cart_schema import CartResponse
from src.use_cases.client.add_to_cart import AddToCartUseCase
from src.use_cases.client.create_client import CreateClientUseCase
from src.use_cases.client.deactivate_client import DeactivateClientUseCase
from src.use_cases.client.get_client_by_cpf import GetClientByCpfUseCase
from src.use_cases.client.get_client_by_id import GetClientByIdUseCase
from src.use_cases.client.get_client_by_user_id import GetClientByUserIdUseCase
from src.use_cases.client.list_client_orders import ListClientOrdersUseCase
from src.use_cases.client.update_client import UpdateClientUseCase

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(payload: ClientCreate, db: Session = Depends(get_db)):
    def _execute():
        user_repository = UserRepository(db)
        client_repository = ClientRepository(db)
        use_case = CreateClientUseCase(user_repository, client_repository)
        client = use_case.execute(
            nome=payload.nome,
            email=payload.email,
            senha=payload.senha,
            cpf=payload.cpf,
            telefone=payload.telefone,
        )
        return to_client_response(client)

    return run_use_case(_execute)


@router.get("/user/{user_id}", response_model=ClientResponse)
def get_client_by_user_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_client_access_by_user_id(user_id, current_user)
    def _execute():
        repository = ClientRepository(db)
        use_case = GetClientByUserIdUseCase(repository)
        return to_client_response(use_case.execute(user_id))

    return run_use_case(_execute)


@router.get("/cpf/{cpf}", response_model=ClientResponse)
def get_client_by_cpf(
    cpf: str,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_client_access_by_cpf(cpf, current_user, db)
    def _execute():
        repository = ClientRepository(db)
        use_case = GetClientByCpfUseCase(repository)
        return to_client_response(use_case.execute(cpf))

    return run_use_case(_execute)


@router.get("/{client_id}", response_model=ClientResponse)
def get_client_by_id(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_client_owner_or_admin(client_id, current_user, db)
    def _execute():
        repository = ClientRepository(db)
        use_case = GetClientByIdUseCase(repository)
        return to_client_response(use_case.execute(client_id))

    return run_use_case(_execute)


@router.put("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: int,
    payload: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_client_owner_or_admin(client_id, current_user, db)
    def _execute():
        repository = ClientRepository(db)
        use_case = UpdateClientUseCase(repository)
        client = use_case.execute(
            client_id=client_id,
            nome=payload.nome,
            telefone=payload.telefone,
            cpf=payload.cpf,
        )
        return to_client_response(client)

    return run_use_case(_execute)


@router.patch("/{client_id}/deactivate", response_model=ClientResponse)
def deactivate_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_client_owner_or_admin(client_id, current_user, db)
    def _execute():
        repository = ClientRepository(db)
        use_case = DeactivateClientUseCase(repository)
        return to_client_response(use_case.execute(client_id))

    return run_use_case(_execute)


@router.get("/{client_id}/orders", response_model=list[OrderListResponse])
def list_client_orders(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_client_owner_or_admin(client_id, current_user, db)
    # TODO: integração completa quando ListClientOrdersUseCase usar OrderRepository
    def _execute():
        repository = ClientRepository(db)
        use_case = ListClientOrdersUseCase(repository)
        orders = use_case.execute(client_id)
        return [to_order_list_response(order) for order in orders]

    return run_use_case(_execute)


@router.post("/{client_id}/cart/items", response_model=CartResponse)
def add_to_cart(
    client_id: int,
    payload: ClientCartAdd,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_client_owner_or_admin(client_id, current_user, db)
    def _execute():
        use_case = AddToCartUseCase(
            ClientRepository(db),
            CartRepository(db),
            CartItemRepository(db),
            ProductRepository(db),
        )
        cart = use_case.execute(client_id, payload.produto_id, payload.quantidade)
        return to_cart_response(cart)

    return run_use_case(_execute)
