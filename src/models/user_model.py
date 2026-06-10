from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from src.database.database import Base


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    senha_hash = Column(String(255), nullable=False)
    telefone = Column(String(20), nullable=True)
    data_cadastro = Column(DateTime, default=datetime.utcnow, nullable=False)
    role = Column(String(20), default="CLIENTE", nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
