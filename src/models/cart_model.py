from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from src.database.database import Base


class CartModel(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(
        Integer, ForeignKey("clients.id"), unique=True, nullable=False, index=True
    )
    data_criacao = Column(DateTime, default=datetime.utcnow, nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)

    client = relationship("ClientModel", backref="cart", uselist=False)
    itens = relationship(
        "CartItemModel",
        back_populates="cart",
        cascade="all, delete-orphan",
    )
