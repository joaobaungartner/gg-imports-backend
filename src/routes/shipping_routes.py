from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.routes.utils import run_use_case
from src.schemas.shipping_schema import ShippingQuoteRequest, ShippingQuoteResponse
from src.use_cases.shipping.calculate_shipping import CalculateShippingUseCase

router = APIRouter(prefix="/shipping", tags=["Shipping"])


@router.post("/quote", response_model=ShippingQuoteResponse)
def quote_shipping(payload: ShippingQuoteRequest, db: Session = Depends(get_db)):
    del db

    def _execute():
        use_case = CalculateShippingUseCase()
        return use_case.execute(
            cep=payload.cep,
            shipping_method=payload.shipping_method,
            item_count=payload.item_count,
        )

    return run_use_case(_execute)
