from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routes.auth_routes import router as auth_router
from src.routes.address_routes import router as address_router
from src.routes.admin_routes import router as admin_router
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

app = FastAPI(
    title="GG Imports API",
    description="API do ecommerce de camisas de time GG Imports",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(client_router)
app.include_router(admin_router)
app.include_router(category_router)
app.include_router(product_router)
app.include_router(cart_router)
app.include_router(cart_item_router)
app.include_router(order_router)
app.include_router(order_item_router)
app.include_router(address_router)
app.include_router(coupon_router)
app.include_router(payment_router)


@app.get("/")
def root():
    return {"message": "GG Imports API", "docs": "/docs"}
