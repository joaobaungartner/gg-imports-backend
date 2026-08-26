from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from src.database.database import Base


class StockMovementModel(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    movement_type = Column(String(30), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    previous_stock = Column(Integer, nullable=False)
    new_stock = Column(Integer, nullable=False)
    reason = Column(String(500), nullable=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True, index=True)
    changed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
