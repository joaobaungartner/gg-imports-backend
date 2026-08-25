from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.entities.user import UserEntity
from src.middlewares.auth import get_current_admin
from src.repositories.category_repository import CategoryRepository
from src.repositories.product_collection_repository import ProductCollectionRepository
from src.repositories.product_repository import ProductRepository
from src.routes.utils import run_use_case
from src.schemas.collection_schema import (
    ProductCollectionResponse,
    ProductCollectionUpdate,
)
from src.use_cases.product.manage_product_collections import (
    GetAdminProductCollectionUseCase,
    UpdateAdminProductCollectionUseCase,
)

router = APIRouter(prefix="/admin/product-collections", tags=["Admin Product Collections"])


@router.get("/{slug}", response_model=ProductCollectionResponse)
def get_admin_product_collection(
    slug: str,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = GetAdminProductCollectionUseCase(
            ProductCollectionRepository(db),
            ProductRepository(db),
            CategoryRepository(db),
        )
        return use_case.execute(slug)

    return run_use_case(_execute)


@router.put("/{slug}", response_model=ProductCollectionResponse)
def update_admin_product_collection(
    slug: str,
    payload: ProductCollectionUpdate,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = UpdateAdminProductCollectionUseCase(
            ProductCollectionRepository(db),
            ProductRepository(db),
            CategoryRepository(db),
        )
        return use_case.execute(slug, payload.group_keys)

    return run_use_case(_execute)
