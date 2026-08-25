from src.models.product_collection_model import (
    ProductCollectionItemModel,
    ProductCollectionModel,
)
from src.models.product_model import ProductModel
from src.utils.product_group_key import build_product_group_key
from sqlalchemy.orm import Session


class ProductCollectionRepository:
    VALID_SLUGS = {"promotions", "launches"}

    def __init__(self, db: Session):
        self.db = db

    def get_collection_by_slug(self, slug: str) -> ProductCollectionModel | None:
        return (
            self.db.query(ProductCollectionModel)
            .filter(ProductCollectionModel.slug == slug)
            .first()
        )

    def get_group_keys(self, slug: str) -> set[str]:
        collection = self.get_collection_by_slug(slug)
        if not collection:
            return set()
        rows = (
            self.db.query(ProductCollectionItemModel.group_key)
            .filter(ProductCollectionItemModel.collection_id == collection.id)
            .all()
        )
        return {row[0] for row in rows}

    def replace_group_keys(self, slug: str, group_keys: list[str]) -> list[str]:
        if slug not in self.VALID_SLUGS:
            raise ValueError("Coleção inválida")

        collection = self.get_collection_by_slug(slug)
        if not collection:
            raise ValueError("Coleção não encontrada")

        normalized: list[str] = []
        seen: set[str] = set()
        for key in group_keys:
            value = (key or "").strip()
            if not value or value in seen:
                continue
            if len(value) > 512:
                raise ValueError("Chave de produto inválida")
            seen.add(value)
            normalized.append(value)

        try:
            (
                self.db.query(ProductCollectionItemModel)
                .filter(ProductCollectionItemModel.collection_id == collection.id)
                .delete(synchronize_session=False)
            )
            for key in normalized:
                self.db.add(
                    ProductCollectionItemModel(
                        collection_id=collection.id,
                        group_key=key,
                    )
                )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return normalized

    def list_products_in_collection(
        self,
        slug: str,
        *,
        active_only: bool = True,
    ) -> list[ProductModel]:
        group_keys = self.get_group_keys(slug)
        if not group_keys:
            return []

        query = self.db.query(ProductModel)
        if active_only:
            query = query.filter(ProductModel.ativo.is_(True))

        models = query.all()
        matched: list[ProductModel] = []
        for model in models:
            key = build_product_group_key(
                nome=model.nome,
                clube=model.clube,
                category_id=model.category_id,
                tipo=model.tipo,
                imagem_url=model.imagem_url,
                preco=model.preco,
            )
            if key in group_keys:
                matched.append(model)
        return matched
