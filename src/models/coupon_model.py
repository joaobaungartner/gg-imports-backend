from sqlalchemy import Boolean, Column, Date, Integer, Numeric, String
from sqlalchemy.orm import relationship

from src.database.database import Base


class CouponModel(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), unique=True, nullable=False, index=True)
    desconto = Column(Numeric(5, 2), nullable=False)
    validade = Column(Date, nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)

    orders = relationship("OrderModel", back_populates="cupom")
