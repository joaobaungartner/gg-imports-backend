from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from src.database.database import Base


class AddressModel(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(
        Integer, ForeignKey("clients.id"), nullable=False, index=True
    )
    rua = Column(String(255), nullable=False)
    numero = Column(String(20), nullable=False)
    bairro = Column(String(100), nullable=False)
    cidade = Column(String(100), nullable=False)
    estado = Column(String(2), nullable=False)
    cep = Column(String(8), nullable=False, index=True)
    ativo = Column(Boolean, default=True, nullable=False)

    client = relationship("ClientModel", backref="addresses")
