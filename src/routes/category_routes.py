from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.entities.user import UserEntity
from src.middlewares.auth import get_current_admin
from src.repositories.category_repository import CategoryRepository
from src.routes.mappers import to_category_list_response, to_category_response
from src.routes.utils import run_use_case
from src.schemas.category_schema import (
    CategoryCreate,
    CategoryListResponse,
    CategoryResponse,
    CategoryUpdate,
)
from src.use_cases.category.activate_category import ActivateCategoryUseCase
from src.use_cases.category.create_category import CreateCategoryUseCase
from src.use_cases.category.deactivate_category import DeactivateCategoryUseCase
from src.use_cases.category.delete_category import DeleteCategoryUseCase
from src.use_cases.category.get_category_by_id import GetCategoryByIdUseCase
from src.use_cases.category.get_category_by_name import GetCategoryByNameUseCase
from src.use_cases.category.list_categories import ListCategoriesUseCase
from src.use_cases.category.update_category import UpdateCategoryUseCase

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        repository = CategoryRepository(db)
        use_case = CreateCategoryUseCase(repository)
        category = use_case.execute(nome=payload.nome, descricao=payload.descricao)
        return to_category_response(category)

    return run_use_case(_execute)


@router.get("/", response_model=list[CategoryListResponse])
def list_categories(
    active: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    def _execute():
        repository = CategoryRepository(db)
        use_case = ListCategoriesUseCase(repository)
        categories = use_case.execute(ativo=active)
        return [to_category_list_response(category) for category in categories]

    return run_use_case(_execute)


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category_by_id(category_id: int, db: Session = Depends(get_db)):
    def _execute():
        repository = CategoryRepository(db)
        use_case = GetCategoryByIdUseCase(repository)
        return to_category_response(use_case.execute(category_id))

    return run_use_case(_execute)


@router.get("/name/{nome}", response_model=CategoryResponse)
def get_category_by_name(nome: str, db: Session = Depends(get_db)):
    def _execute():
        repository = CategoryRepository(db)
        use_case = GetCategoryByNameUseCase(repository)
        return to_category_response(use_case.execute(nome))

    return run_use_case(_execute)


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        repository = CategoryRepository(db)
        use_case = UpdateCategoryUseCase(repository)
        category = use_case.execute(
            category_id=category_id,
            nome=payload.nome,
            descricao=payload.descricao,
            ativo=payload.ativo,
        )
        return to_category_response(category)

    return run_use_case(_execute)


@router.patch("/{category_id}/activate", response_model=CategoryResponse)
def activate_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        repository = CategoryRepository(db)
        use_case = ActivateCategoryUseCase(repository)
        return to_category_response(use_case.execute(category_id))

    return run_use_case(_execute)


@router.patch("/{category_id}/deactivate", response_model=CategoryResponse)
def deactivate_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        repository = CategoryRepository(db)
        use_case = DeactivateCategoryUseCase(repository)
        return to_category_response(use_case.execute(category_id))

    return run_use_case(_execute)


@router.delete("/{category_id}", response_model=CategoryResponse)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        from src.repositories.product_repository import ProductRepository

        use_case = DeleteCategoryUseCase(
            CategoryRepository(db), ProductRepository(db)
        )
        return to_category_response(use_case.execute(category_id))

    return run_use_case(_execute)
