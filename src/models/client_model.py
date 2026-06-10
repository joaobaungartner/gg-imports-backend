from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from src.database.database import Base


class ClientModel(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True
    )
    cpf = Column(String(11), unique=True, nullable=False, index=True)
    ativo = Column(Boolean, default=True, nullable=False)

    user = relationship("UserModel", backref="client", uselist=False)
