from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from src.database.database import Base


class ProductCollectionModel(Base):
    __tablename__ = "product_collections"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)

    items = relationship(
        "ProductCollectionItemModel",
        back_populates="collection",
        cascade="all, delete-orphan",
    )


class ProductCollectionItemModel(Base):
    __tablename__ = "product_collection_items"
    __table_args__ = (
        UniqueConstraint(
            "collection_id",
            "group_key",
            name="uq_collection_group_key",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    collection_id = Column(
        Integer,
        ForeignKey("product_collections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    group_key = Column(String(512), nullable=False, index=True)

    collection = relationship("ProductCollectionModel", back_populates="items")
