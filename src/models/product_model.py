from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from src.database.database import Base


class ProductModel(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(
        Integer, ForeignKey("categories.id"), nullable=False, index=True
    )
    nome = Column(String(255), nullable=False, index=True)
    descricao = Column(Text, nullable=True)
    preco = Column(Numeric(10, 2), nullable=False)
    tamanho = Column(String(10), nullable=False)
    clube = Column(String(100), nullable=False, index=True)
    tipo = Column(String(50), nullable=False, index=True)
    estoque = Column(Integer, nullable=False, default=0)
    imagem_url = Column(String(500), nullable=True)
    ativo = Column(Boolean, default=True, nullable=False)

    categoria = relationship("CategoryModel", back_populates="produtos")
    cart_items = relationship("CartItemModel", back_populates="produto")
    order_items = relationship("OrderItemModel", back_populates="produto")
