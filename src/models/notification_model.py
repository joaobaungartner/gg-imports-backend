from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from src.database.database import Base


class NotificationModel(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    channel = Column(String(20), nullable=False, index=True)
    event = Column(String(50), nullable=False, index=True)
    recipient = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=True)
    body = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="PENDING", index=True)
    attempts = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
