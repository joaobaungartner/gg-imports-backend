from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.entities.user import UserEntity
from src.middlewares.auth import get_current_admin
from src.repositories.site_content_repository import SiteContentRepository
from src.routes.utils import run_use_case
from src.schemas.collection_schema import HowToBuyContent
from src.use_cases.site_content.manage_how_to_buy import (
    GetHowToBuyContentUseCase,
    UpdateHowToBuyContentUseCase,
)

public_router = APIRouter(prefix="/site-content", tags=["Site Content"])
admin_router = APIRouter(prefix="/admin/site-content", tags=["Admin Site Content"])


@public_router.get("/how-to-buy", response_model=HowToBuyContent)
def get_how_to_buy(db: Session = Depends(get_db)):
    def _execute():
        use_case = GetHowToBuyContentUseCase(SiteContentRepository(db))
        return use_case.execute()

    return run_use_case(_execute)


@admin_router.put("/how-to-buy", response_model=HowToBuyContent)
def update_how_to_buy(
    payload: HowToBuyContent,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = UpdateHowToBuyContentUseCase(SiteContentRepository(db))
        return use_case.execute(payload.model_dump())

    return run_use_case(_execute)
