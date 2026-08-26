from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from src.database.database import Base


class PostSaleRequestModel(Base):
    __tablename__ = "post_sale_requests"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    request_type = Column(String(20), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="REQUESTED", index=True)
    admin_note = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
