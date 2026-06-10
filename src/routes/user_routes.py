from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.entities.user import UserRole
from src.repositories.user_repository import UserRepository
from src.routes.mappers import to_user_response
from src.routes.utils import run_use_case
from src.schemas.user_schema import UserCreate, UserLogin, UserResponse, UserUpdate
from src.use_cases.user.authenticate_user import AuthenticateUserUseCase
from src.use_cases.user.create_user import CreateUserUseCase
from src.use_cases.user.deactivate_user import DeactivateUserUseCase
from src.use_cases.user.get_user_by_email import GetUserByEmailUseCase
from src.use_cases.user.get_user_by_id import GetUserByIdUseCase
from src.use_cases.user.update_user import UpdateUserUseCase

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/login", response_model=UserResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    # TODO: retornar JWT após implementar autenticação
    def _execute():
        repository = UserRepository(db)
        use_case = AuthenticateUserUseCase(repository)
        return to_user_response(use_case.execute(payload.email, payload.senha))

    return run_use_case(_execute)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    # TODO: proteger criação de usuários com role ADMIN quando autenticação existir
    def _execute():
        repository = UserRepository(db)
        use_case = CreateUserUseCase(repository)
        role = UserRole(payload.role) if payload.role else UserRole.CLIENTE
        user = use_case.execute(
            nome=payload.nome,
            email=payload.email,
            senha=payload.senha,
            telefone=payload.telefone,
            role=role,
        )
        return to_user_response(user)

    return run_use_case(_execute)


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    def _execute():
        repository = UserRepository(db)
        use_case = GetUserByIdUseCase(repository)
        return to_user_response(use_case.execute(user_id))

    return run_use_case(_execute)


@router.get("/email/{email}", response_model=UserResponse)
def get_user_by_email(email: str, db: Session = Depends(get_db)):
    def _execute():
        repository = UserRepository(db)
        use_case = GetUserByEmailUseCase(repository)
        return to_user_response(use_case.execute(email))

    return run_use_case(_execute)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    def _execute():
        repository = UserRepository(db)
        use_case = UpdateUserUseCase(repository)
        user = use_case.execute(
            user_id=user_id,
            nome=payload.nome,
            telefone=payload.telefone,
        )
        return to_user_response(user)

    return run_use_case(_execute)


@router.patch("/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user(user_id: int, db: Session = Depends(get_db)):
    def _execute():
        repository = UserRepository(db)
        use_case = DeactivateUserUseCase(repository)
        return to_user_response(use_case.execute(user_id))

    return run_use_case(_execute)
