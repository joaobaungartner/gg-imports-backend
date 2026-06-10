from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship

from src.database.database import Base


class CartItemModel(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(
        Integer, ForeignKey("carts.id"), nullable=False, index=True
    )
    product_id = Column(
        Integer, ForeignKey("products.id"), nullable=False, index=True
    )
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Numeric(10, 2), nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)

    cart = relationship("CartModel", back_populates="itens")
    produto = relationship("ProductModel", back_populates="cart_items")
