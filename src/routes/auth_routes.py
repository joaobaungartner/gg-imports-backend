from datetime import timedelta
from hashlib import sha256

from fastapi import APIRouter, Depends, HTTPException
from jose import JWTError
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.entities.user import UserEntity, UserRole
from src.middlewares.auth import get_current_user
from src.repositories.address_repository import AddressRepository
from src.repositories.client_repository import ClientRepository
from src.repositories.user_repository import UserRepository
from src.repositories.notification_repository import NotificationRepository
from src.routes.mappers import to_address_list_response, to_user_response
from src.routes.utils import run_use_case
from src.schemas.auth_schema import (
    AuthLogin, AuthMeResponse, ChangePassword, EmailRequest,
    PasswordResetConfirm, TokenAction, TokenResponse,
)
from src.config.config import get_settings
from src.services.notification_service import NotificationService
from src.utils.jwt import create_access_token, decode_access_token
from src.utils.password import hash_password, verify_password
from src.use_cases.auth.login_with_jwt import LoginWithJwtUseCase
from src.use_cases.user.authenticate_user import AuthenticateUserUseCase

router = APIRouter(prefix="/auth", tags=["Auth"])


def _password_fingerprint(password_hash: str) -> str:
    return sha256(password_hash.encode()).hexdigest()[:16]


def _decode_action_token(token: str, purpose: str) -> dict:
    try:
        payload = decode_access_token(token)
    except JWTError as exc:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado") from exc
    if payload.get("purpose") != purpose:
        raise HTTPException(status_code=400, detail="Token inválido")
    return payload


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
            email_verificado=current_user.email_verificado,
        )

    return run_use_case(_execute)


@router.post("/password/forgot")
def forgot_password(payload: EmailRequest, db: Session = Depends(get_db)):
    user = UserRepository(db).get_by_email(payload.email.lower())
    if user and user.ativo:
        settings = get_settings()
        token = create_access_token(
            {"sub": str(user.id), "purpose": "password_reset",
             "fp": _password_fingerprint(user.senha_hash)},
            timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES),
        )
        link = f"{settings.FRONTEND_BASE_URL}/redefinir-senha?token={token}"
        NotificationService(NotificationRepository(db)).email(
            "PASSWORD_RESET", user.email, "Redefinição de senha — GG Imports",
            f"Use este link para redefinir sua senha: {link}",
        )
    return {"message": "Se o e-mail estiver cadastrado, enviaremos as instruções."}


@router.post("/password/reset")
def reset_password(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    token = _decode_action_token(payload.token, "password_reset")
    user = UserRepository(db).get_by_id(int(token["sub"]))
    if not user or token.get("fp") != _password_fingerprint(user.senha_hash):
        raise HTTPException(status_code=400, detail="Token inválido ou já utilizado")
    UserRepository(db).update(user.id, {"senha_hash": hash_password(payload.nova_senha)})
    return {"message": "Senha alterada com sucesso."}


@router.post("/password/change")
def change_password(
    payload: ChangePassword,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    if not verify_password(payload.senha_atual, current_user.senha_hash):
        raise HTTPException(status_code=400, detail="Senha atual incorreta")
    UserRepository(db).update(
        current_user.id, {"senha_hash": hash_password(payload.nova_senha)}
    )
    return {"message": "Senha alterada com sucesso."}


@router.post("/email/request-verification")
def request_email_verification(
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    if current_user.email_verificado:
        return {"message": "E-mail já verificado."}
    settings = get_settings()
    token = create_access_token(
        {"sub": str(current_user.id), "purpose": "email_verify",
         "email": current_user.email},
        timedelta(hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS),
    )
    link = f"{settings.FRONTEND_BASE_URL}/verificar-email?token={token}"
    NotificationService(NotificationRepository(db)).email(
        "EMAIL_VERIFICATION", current_user.email, "Confirme seu e-mail — GG Imports",
        f"Confirme seu e-mail acessando: {link}",
    )
    return {"message": "Verificação enviada."}


@router.post("/email/verify")
def verify_email(payload: TokenAction, db: Session = Depends(get_db)):
    token = _decode_action_token(payload.token, "email_verify")
    user = UserRepository(db).get_by_id(int(token["sub"]))
    if not user or token.get("email") != user.email:
        raise HTTPException(status_code=400, detail="Token inválido")
    UserRepository(db).update(user.id, {"email_verificado": True})
    return {"message": "E-mail verificado com sucesso."}
