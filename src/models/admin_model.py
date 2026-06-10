from sqlalchemy import Boolean, Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from src.database.database import Base


class AdminModel(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True
    )
    ativo = Column(Boolean, default=True, nullable=False)

    user = relationship("UserModel", backref="admin", uselist=False)
