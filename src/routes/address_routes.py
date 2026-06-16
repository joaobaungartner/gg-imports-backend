from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.entities.user import UserEntity
from src.middlewares.auth import (
    ensure_address_owner_or_admin,
    ensure_client_owner_or_admin,
    get_current_admin,
    get_current_user,
)
from src.repositories.address_repository import AddressRepository
from src.repositories.client_repository import ClientRepository
from src.routes.mappers import to_address_list_response, to_address_response
from src.routes.utils import run_use_case
from src.schemas.address_schema import (
    AddressCreate,
    AddressListResponse,
    AddressResponse,
    AddressUpdate,
)
from src.use_cases.address.create_address import CreateAddressUseCase
from src.use_cases.address.deactivate_address import DeactivateAddressUseCase
from src.use_cases.address.get_address_by_id import GetAddressByIdUseCase
from src.use_cases.address.get_addresses_by_client import GetAddressesByClientUseCase
from src.use_cases.address.list_addresses import ListAddressesUseCase
from src.use_cases.address.update_address import UpdateAddressUseCase
from src.use_cases.address.validate_address_for_order import (
    ValidateAddressForOrderUseCase,
)


class ValidateAddressRequest(BaseModel):
    client_id: int = Field(..., gt=0)


router = APIRouter(prefix="/addresses", tags=["Addresses"])


@router.post("/", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
def create_address(
    payload: AddressCreate,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_client_owner_or_admin(payload.client_id, current_user, db)

    def _execute():
        use_case = CreateAddressUseCase(
            ClientRepository(db), AddressRepository(db)
        )
        address = use_case.execute(
            client_id=payload.client_id,
            rua=payload.rua,
            numero=payload.numero,
            bairro=payload.bairro,
            cidade=payload.cidade,
            estado=payload.estado,
            cep=payload.cep,
        )
        return to_address_response(address)

    return run_use_case(_execute)


@router.get("/", response_model=list[AddressListResponse])
def list_addresses(
    active: bool | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = ListAddressesUseCase(AddressRepository(db))
        addresses = use_case.execute(ativo=active)
        return [to_address_list_response(address) for address in addresses]

    return run_use_case(_execute)


@router.get("/client/{client_id}", response_model=list[AddressListResponse])
def get_addresses_by_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_client_owner_or_admin(client_id, current_user, db)

    def _execute():
        use_case = GetAddressesByClientUseCase(
            ClientRepository(db), AddressRepository(db)
        )
        addresses = use_case.execute(client_id)
        return [to_address_list_response(address) for address in addresses]

    return run_use_case(_execute)


@router.get("/{address_id}", response_model=AddressResponse)
def get_address_by_id(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_address_owner_or_admin(address_id, current_user, db)

    def _execute():
        use_case = GetAddressByIdUseCase(AddressRepository(db))
        return to_address_response(use_case.execute(address_id))

    return run_use_case(_execute)


@router.put("/{address_id}", response_model=AddressResponse)
def update_address(
    address_id: int,
    payload: AddressUpdate,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_address_owner_or_admin(address_id, current_user, db)

    def _execute():
        use_case = UpdateAddressUseCase(AddressRepository(db))
        address = use_case.execute(
            address_id=address_id,
            rua=payload.rua,
            numero=payload.numero,
            bairro=payload.bairro,
            cidade=payload.cidade,
            estado=payload.estado,
            cep=payload.cep,
        )
        return to_address_response(address)

    return run_use_case(_execute)


@router.post("/{address_id}/validate-for-order", response_model=AddressResponse)
def validate_address_for_order(
    address_id: int,
    payload: ValidateAddressRequest,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_address_owner_or_admin(address_id, current_user, db)
    ensure_client_owner_or_admin(payload.client_id, current_user, db)

    def _execute():
        use_case = ValidateAddressForOrderUseCase(AddressRepository(db))
        return to_address_response(
            use_case.execute(address_id, payload.client_id)
        )

    return run_use_case(_execute)


@router.patch("/{address_id}/deactivate", response_model=AddressResponse)
def deactivate_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    ensure_address_owner_or_admin(address_id, current_user, db)

    def _execute():
        use_case = DeactivateAddressUseCase(AddressRepository(db))
        return to_address_response(use_case.execute(address_id))

    return run_use_case(_execute)
