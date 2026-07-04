from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.entities.user import UserEntity, UserRole
from src.middlewares.auth import get_current_user
from src.repositories.address_repository import AddressRepository
from src.repositories.client_repository import ClientRepository
from src.repositories.user_repository import UserRepository
from src.routes.mappers import to_address_list_response, to_user_response
from src.routes.utils import run_use_case
from src.schemas.auth_schema import AuthLogin, AuthMeResponse, TokenResponse
from src.use_cases.auth.login_with_jwt import LoginWithJwtUseCase
from src.use_cases.user.authenticate_user import AuthenticateUserUseCase

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: AuthLogin, db: Session = Depends(get_db)):
    try:
        user_repository = UserRepository(db)
        authenticate_use_case = AuthenticateUserUseCase(user_repository)
        login_use_case = LoginWithJwtUseCase(authenticate_use_case)
        result = login_use_case.execute(payload.email, payload.senha)
        return TokenResponse(
            access_token=result.access_token,
            token_type=result.token_type,
            expires_in=result.expires_in,
            user=to_user_response(result.user),
        )
    except ValueError as error:
        message = str(error)
        if "inativo" in message.lower():
            raise HTTPException(status_code=403, detail=message) from error
        raise HTTPException(status_code=401, detail=message) from error


@router.get("/me", response_model=AuthMeResponse)
def get_current_profile(
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    def _execute():
        user_response = to_user_response(current_user)
        client_id = None
        cpf = None
        endereco = None

        if current_user.role == UserRole.CLIENTE:
            client = ClientRepository(db).get_by_user_id(current_user.id)
            if client:
                client_id = client.client_id
                cpf = client.cpf
                addresses = AddressRepository(db).get_by_client_id(client.client_id)
                active_addresses = [address for address in addresses if address.ativo]
                if active_addresses:
                    endereco = to_address_list_response(active_addresses[0])

        return AuthMeResponse(
            id=user_response.id,
            nome=user_response.nome,
            email=user_response.email,
            telefone=user_response.telefone,
            role=user_response.role,
            ativo=user_response.ativo,
            data_cadastro=user_response.data_cadastro,
            client_id=client_id,
            cpf=cpf,
            endereco=endereco,
        )

    return run_use_case(_execute)
