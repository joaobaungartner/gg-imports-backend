from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.entities.user import UserEntity
from src.middlewares.auth import get_current_admin, get_current_user
from src.repositories.category_repository import CategoryRepository
from src.repositories.order_item_repository import OrderItemRepository
from src.repositories.product_repository import ProductRepository
from src.routes.mappers import (
    to_product_availability_response,
    to_product_list_response,
    to_product_response,
)
from src.routes.utils import run_use_case
from src.schemas.product_schema import (
    ProductAvailabilityResponse,
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductStockChange,
    ProductStockUpdate,
    ProductUpdate,
)
from src.use_cases.product.activate_product import ActivateProductUseCase
from src.use_cases.product.check_product_availability import (
    CheckProductAvailabilityUseCase,
)
from src.use_cases.product.create_product import CreateProductUseCase
from src.use_cases.product.deactivate_product import DeactivateProductUseCase
from src.use_cases.product.decrease_product_stock import DecreaseProductStockUseCase
from src.use_cases.product.delete_product import DeleteProductUseCase
from src.use_cases.product.get_product_by_id import GetProductByIdUseCase
from src.use_cases.product.get_product_by_name import GetProductByNameUseCase
from src.use_cases.product.increase_product_stock import IncreaseProductStockUseCase
from src.use_cases.product.list_products import ListProductsUseCase
from src.use_cases.product.list_products_by_category import ListProductsByCategoryUseCase
from src.use_cases.product.search_products import SearchProductsUseCase
from src.use_cases.product.update_product import UpdateProductUseCase
from src.use_cases.product.update_product_stock import UpdateProductStockUseCase

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = CreateProductUseCase(
            CategoryRepository(db), ProductRepository(db)
        )
        product = use_case.execute(
            category_id=payload.category_id,
            nome=payload.nome,
            preco=payload.preco,
            tamanho=payload.tamanho,
            clube=payload.clube,
            tipo=payload.tipo,
            descricao=payload.descricao,
            estoque=payload.estoque,
            imagem_url=payload.imagem_url,
            ativo=payload.ativo if payload.ativo is not None else True,
        )
        return to_product_response(product)

    return run_use_case(_execute)


@router.get("/", response_model=list[ProductListResponse])
def list_products(
    active: bool | None = Query(default=None),
    category_id: int | None = Query(default=None),
    clube: str | None = Query(default=None),
    tipo: str | None = Query(default=None),
    tamanho: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    def _execute():
        use_case = ListProductsUseCase(ProductRepository(db))
        products = use_case.execute(
            ativo=active,
            category_id=category_id,
            clube=clube,
            tipo=tipo,
            tamanho=tamanho,
        )
        return [to_product_list_response(product) for product in products]

    return run_use_case(_execute)


@router.get("/search", response_model=list[ProductListResponse])
def search_products(
    q: str = Query(..., min_length=1),
    apenas_ativos: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    def _execute():
        use_case = SearchProductsUseCase(ProductRepository(db))
        products = use_case.execute(q, apenas_ativos=apenas_ativos)
        return [to_product_list_response(product) for product in products]

    return run_use_case(_execute)


@router.get("/category/{category_id}", response_model=list[ProductListResponse])
def list_products_by_category(category_id: int, db: Session = Depends(get_db)):
    def _execute():
        use_case = ListProductsByCategoryUseCase(
            CategoryRepository(db), ProductRepository(db)
        )
        products = use_case.execute(category_id)
        return [to_product_list_response(product) for product in products]

    return run_use_case(_execute)


@router.get("/name/{nome}", response_model=ProductResponse)
def get_product_by_name(nome: str, db: Session = Depends(get_db)):
    def _execute():
        use_case = GetProductByNameUseCase(ProductRepository(db))
        return to_product_response(use_case.execute(nome))

    return run_use_case(_execute)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product_by_id(product_id: int, db: Session = Depends(get_db)):
    def _execute():
        use_case = GetProductByIdUseCase(ProductRepository(db))
        return to_product_response(use_case.execute(product_id))

    return run_use_case(_execute)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = UpdateProductUseCase(
            CategoryRepository(db), ProductRepository(db)
        )
        product = use_case.execute(
            product_id=product_id,
            category_id=payload.category_id,
            nome=payload.nome,
            descricao=payload.descricao,
            preco=payload.preco,
            tamanho=payload.tamanho,
            clube=payload.clube,
            tipo=payload.tipo,
            estoque=payload.estoque,
            imagem_url=payload.imagem_url,
            ativo=payload.ativo,
        )
        return to_product_response(product)

    return run_use_case(_execute)


@router.patch("/{product_id}/stock", response_model=ProductResponse)
def update_product_stock(
    product_id: int,
    payload: ProductStockUpdate,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = UpdateProductStockUseCase(ProductRepository(db))
        return to_product_response(use_case.execute(product_id, payload.estoque))

    return run_use_case(_execute)


@router.patch("/{product_id}/stock/increase", response_model=ProductResponse)
def increase_product_stock(
    product_id: int,
    payload: ProductStockChange,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = IncreaseProductStockUseCase(ProductRepository(db))
        return to_product_response(
            use_case.execute(product_id, payload.quantidade)
        )

    return run_use_case(_execute)


@router.patch("/{product_id}/stock/decrease", response_model=ProductResponse)
def decrease_product_stock(
    product_id: int,
    payload: ProductStockChange,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = DecreaseProductStockUseCase(ProductRepository(db))
        return to_product_response(
            use_case.execute(product_id, payload.quantidade)
        )

    return run_use_case(_execute)


@router.post("/{product_id}/availability", response_model=ProductAvailabilityResponse)
def check_product_availability(
    product_id: int,
    payload: ProductStockChange,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_user),
):
    def _execute():
        use_case = CheckProductAvailabilityUseCase(ProductRepository(db))
        result = use_case.execute(product_id, payload.quantidade)
        return to_product_availability_response(result)

    return run_use_case(_execute)


@router.patch("/{product_id}/activate", response_model=ProductResponse)
def activate_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = ActivateProductUseCase(ProductRepository(db))
        return to_product_response(use_case.execute(product_id))

    return run_use_case(_execute)


@router.patch("/{product_id}/deactivate", response_model=ProductResponse)
def deactivate_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = DeactivateProductUseCase(ProductRepository(db))
        return to_product_response(use_case.execute(product_id))

    return run_use_case(_execute)


@router.delete("/{product_id}", response_model=ProductResponse)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    def _execute():
        use_case = DeleteProductUseCase(
            ProductRepository(db), OrderItemRepository(db)
        )
        return to_product_response(use_case.execute(product_id))

    return run_use_case(_execute)
