from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.repositories.user_repository import UserRepository
from src.routes.mappers import to_user_response
from src.schemas.auth_schema import AuthLogin, TokenResponse
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
