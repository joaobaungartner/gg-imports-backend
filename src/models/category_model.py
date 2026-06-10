from sqlalchemy import Boolean, Column, Integer, String, Text
from sqlalchemy.orm import relationship

from src.database.database import Base


class CategoryModel(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), unique=True, nullable=False, index=True)
    descricao = Column(Text, nullable=True)
    ativo = Column(Boolean, default=True, nullable=False)

    produtos = relationship("ProductModel", back_populates="categoria")
