from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from src.routes.auth_routes import router as auth_router
from src.routes.shipping_routes import router as shipping_router
from src.routes.address_routes import router as address_router
from src.routes.admin_routes import router as admin_router
from src.routes.admin_order_routes import router as admin_order_router
from src.routes.admin_management_routes import router as admin_management_router
from src.routes.admin_collection_routes import router as admin_collection_router
from src.routes.site_content_routes import (
    admin_router as admin_site_content_router,
    public_router as site_content_router,
)
from src.routes.cart_item_routes import router as cart_item_router
from src.routes.cart_routes import router as cart_router
from src.routes.category_routes import router as category_router
from src.routes.client_routes import router as client_router
from src.routes.coupon_routes import router as coupon_router
from src.routes.order_item_routes import router as order_item_router
from src.routes.order_routes import router as order_router
from src.routes.payment_routes import router as payment_router
from src.routes.product_routes import router as product_router
from src.routes.user_routes import router as user_router
from src.routes.post_sale_routes import router as post_sale_router, admin_router as admin_post_sale_router
from src.config.config import get_settings
from src.database.database import engine
from src.middlewares.production import ProductionMiddleware, configure_logging

configure_logging()
settings = get_settings()

app = FastAPI(
    title="GG Imports API",
    description="API do ecommerce de camisas de time GG Imports",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ProductionMiddleware)

app.include_router(auth_router)
app.include_router(shipping_router)
app.include_router(user_router)
app.include_router(client_router)
app.include_router(admin_router)
app.include_router(admin_order_router)
app.include_router(admin_management_router)
app.include_router(admin_collection_router)
app.include_router(admin_site_content_router)
app.include_router(site_content_router)
app.include_router(category_router)
app.include_router(product_router)
app.include_router(cart_router)
app.include_router(cart_item_router)
app.include_router(order_router)
app.include_router(order_item_router)
app.include_router(address_router)
app.include_router(coupon_router)
app.include_router(payment_router)
app.include_router(post_sale_router)
app.include_router(admin_post_sale_router)


@app.get("/")
def root():
    return {"message": "GG Imports API", "docs": "/docs"}


@app.get("/health/live", include_in_schema=False)
def health_live():
    return {"status": "ok"}


@app.get("/health/ready", include_in_schema=False)
def health_ready():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok"}
    except Exception:
        return JSONResponse({"status": "unavailable", "database": "error"}, status_code=503)
