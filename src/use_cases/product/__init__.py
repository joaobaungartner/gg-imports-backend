from src.use_cases.product.activate_product import ActivateProductUseCase
from src.use_cases.product.check_product_availability import (
    CheckProductAvailabilityUseCase,
    ProductAvailabilityResult,
)
from src.use_cases.product.create_product import CreateProductUseCase
from src.use_cases.product.deactivate_product import DeactivateProductUseCase
from src.use_cases.product.decrease_product_stock import DecreaseProductStockUseCase
from src.use_cases.product.delete_product import DeleteProductUseCase
from src.use_cases.product.get_product_by_id import GetProductByIdUseCase
from src.use_cases.product.get_product_by_name import GetProductByNameUseCase
from src.use_cases.product.increase_product_stock import IncreaseProductStockUseCase
from src.use_cases.product.list_products import ListProductsUseCase
from src.use_cases.product.list_products_by_category import (
    ListProductsByCategoryUseCase,
)
from src.use_cases.product.search_products import SearchProductsUseCase
from src.use_cases.product.update_product import UpdateProductUseCase
from src.use_cases.product.update_product_stock import UpdateProductStockUseCase

__all__ = [
    "CreateProductUseCase",
    "GetProductByIdUseCase",
    "GetProductByNameUseCase",
    "ListProductsUseCase",
    "ListProductsByCategoryUseCase",
    "SearchProductsUseCase",
    "UpdateProductUseCase",
    "UpdateProductStockUseCase",
    "IncreaseProductStockUseCase",
    "DecreaseProductStockUseCase",
    "ActivateProductUseCase",
    "DeactivateProductUseCase",
    "DeleteProductUseCase",
    "CheckProductAvailabilityUseCase",
    "ProductAvailabilityResult",
]
