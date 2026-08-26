from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from src.database.database import Base


class AdminAuditLogModel(Base):
    __tablename__ = "admin_audit_logs"

    id = Column(Integer, primary_key=True)
    admin_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(80), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(String(80), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
