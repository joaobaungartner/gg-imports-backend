from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.entities.user import UserEntity
from src.middlewares.auth import get_current_admin
from src.repositories.admin_repository import AdminRepository
from src.repositories.user_repository import UserRepository
from src.routes.mappers import to_admin_response
from src.routes.utils import run_use_case
from src.schemas.admin_schema import AdminCreate, AdminResponse, AdminUpdate
from src.use_cases.admin.create_admin import CreateAdminUseCase
from src.use_cases.admin.deactivate_admin import DeactivateAdminUseCase
from src.use_cases.admin.get_admin_by_email import GetAdminByEmailUseCase
from src.use_cases.admin.get_admin_by_id import GetAdminByIdUseCase
from src.use_cases.admin.get_admin_by_user_id import GetAdminByUserIdUseCase
from src.use_cases.admin.update_admin import UpdateAdminUseCase

router = APIRouter(prefix="/admins", tags=["Admins"])


@router.post("/", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
def create_admin(
    payload: AdminCreate,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    # TODO: o primeiro admin deve ser criado via seed, script interno ou variável de ambiente
    def _execute():
        use_case = CreateAdminUseCase(UserRepository(db), AdminRepository(db))
        admin = use_case.execute(
            nome=payload.nome,
            email=payload.email,
            senha=payload.senha,
            telefone=payload.telefone,
        )
        return to_admin_response(admin)

    return run_use_case(_execute)


@router.get("/{admin_id}", response_model=AdminResponse)
def get_admin_by_id(
    admin_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = GetAdminByIdUseCase(AdminRepository(db))
        return to_admin_response(use_case.execute(admin_id))

    return run_use_case(_execute)


@router.get("/user/{user_id}", response_model=AdminResponse)
def get_admin_by_user_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = GetAdminByUserIdUseCase(AdminRepository(db))
        return to_admin_response(use_case.execute(user_id))

    return run_use_case(_execute)


@router.get("/email/{email}", response_model=AdminResponse)
def get_admin_by_email(
    email: str,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = GetAdminByEmailUseCase(AdminRepository(db))
        return to_admin_response(use_case.execute(email))

    return run_use_case(_execute)


@router.put("/{admin_id}", response_model=AdminResponse)
def update_admin(
    admin_id: int,
    payload: AdminUpdate,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = UpdateAdminUseCase(AdminRepository(db))
        admin = use_case.execute(
            admin_id=admin_id,
            nome=payload.nome,
            telefone=payload.telefone,
            email=payload.email,
        )
        return to_admin_response(admin)

    return run_use_case(_execute)


@router.patch("/{admin_id}/deactivate", response_model=AdminResponse)
def deactivate_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = DeactivateAdminUseCase(AdminRepository(db))
        return to_admin_response(use_case.execute(admin_id))

    return run_use_case(_execute)
