from decimal import Decimal

from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.entities.product import ProductEntity
from src.models.product_model import ProductModel


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def _normalize_text(self, value: str) -> str:
        return value.strip()

    def _to_entity(self, model: ProductModel) -> ProductEntity:
        return ProductEntity(
            id=model.id,
            category_id=model.category_id,
            nome=model.nome,
            descricao=model.descricao,
            preco=Decimal(str(model.preco)),
            tamanho=model.tamanho,
            clube=model.clube,
            tipo=model.tipo,
            estoque=model.estoque,
            imagem_url=model.imagem_url,
            ativo=model.ativo,
        )

    def _to_model(self, entity: ProductEntity) -> ProductModel:
        kwargs = {
            "category_id": entity.category_id,
            "nome": self._normalize_text(entity.nome),
            "descricao": entity.descricao,
            "preco": entity.preco,
            "tamanho": self._normalize_text(entity.tamanho),
            "clube": self._normalize_text(entity.clube),
            "tipo": self._normalize_text(entity.tipo),
            "estoque": entity.estoque,
            "imagem_url": entity.imagem_url,
            "ativo": entity.ativo,
        }
        if entity.id is not None:
            kwargs["id"] = entity.id
        return ProductModel(**kwargs)

    def create(self, product: ProductEntity) -> ProductEntity:
        model = self._to_model(product)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def get_by_id(self, product_id: int) -> ProductEntity | None:
        model = (
            self.db.query(ProductModel)
            .filter(ProductModel.id == product_id)
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def get_by_name(self, nome: str) -> ProductEntity | None:
        nome_normalizado = self._normalize_text(nome)
        model = (
            self.db.query(ProductModel)
            .filter(ProductModel.nome == nome_normalizado)
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def list_all(self) -> list[ProductEntity]:
        models = self.db.query(ProductModel).all()
        return [self._to_entity(model) for model in models]

    def list_active(self) -> list[ProductEntity]:
        models = (
            self.db.query(ProductModel)
            .filter(ProductModel.ativo.is_(True))
            .all()
        )
        return [self._to_entity(model) for model in models]

    def list_by_category(self, category_id: int) -> list[ProductEntity]:
        models = (
            self.db.query(ProductModel)
            .filter(ProductModel.category_id == category_id)
            .all()
        )
        return [self._to_entity(model) for model in models]

    def list_by_club(self, clube: str) -> list[ProductEntity]:
        clube_normalizado = self._normalize_text(clube)
        models = (
            self.db.query(ProductModel)
            .filter(ProductModel.clube == clube_normalizado)
            .all()
        )
        return [self._to_entity(model) for model in models]

    def list_by_type(self, tipo: str) -> list[ProductEntity]:
        tipo_normalizado = self._normalize_text(tipo)
        models = (
            self.db.query(ProductModel)
            .filter(ProductModel.tipo == tipo_normalizado)
            .all()
        )
        return [self._to_entity(model) for model in models]

    def search(self, query: str, apenas_ativos: bool = True) -> list[ProductEntity]:
        termo = f"%{query.strip()}%"
        filters = (
            self.db.query(ProductModel)
            .filter(
                or_(
                    ProductModel.nome.ilike(termo),
                    ProductModel.clube.ilike(termo),
                    ProductModel.tipo.ilike(termo),
                    ProductModel.tamanho.ilike(termo),
                    ProductModel.descricao.ilike(termo),
                )
            )
        )
        if apenas_ativos:
            filters = filters.filter(ProductModel.ativo.is_(True))
        models = filters.all()
        return [self._to_entity(model) for model in models]

    def update(self, product_id: int, data: dict) -> ProductEntity | None:
        model = (
            self.db.query(ProductModel)
            .filter(ProductModel.id == product_id)
            .first()
        )
        if not model:
            return None
        for key in ("nome", "tamanho", "clube", "tipo"):
            if key in data:
                data[key] = self._normalize_text(data[key])
        if "descricao" in data and data["descricao"] is not None:
            data["descricao"] = data["descricao"].strip() or None
        if "imagem_url" in data and data["imagem_url"] is not None:
            data["imagem_url"] = data["imagem_url"].strip() or None
        for key, value in data.items():
            if hasattr(model, key):
                setattr(model, key, value)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def update_stock(self, product_id: int, estoque: int) -> ProductEntity | None:
        return self.update(product_id, {"estoque": estoque})

    def increase_stock(
        self, product_id: int, quantidade: int
    ) -> ProductEntity | None:
        product = self.get_by_id(product_id)
        if not product:
            return None
        product.aumentar_estoque(quantidade)
        return self.update_stock(product_id, product.estoque)

    def decrease_stock(
        self, product_id: int, quantidade: int
    ) -> ProductEntity | None:
        product = self.get_by_id(product_id)
        if not product:
            return None
        product.reduzir_estoque(quantidade)
        return self.update_stock(product_id, product.estoque)

    def activate(self, product_id: int) -> ProductEntity | None:
        return self.update(product_id, {"ativo": True})

    def deactivate(self, product_id: int) -> ProductEntity | None:
        return self.update(product_id, {"ativo": False})

    def delete(self, product_id: int) -> bool:
        model = (
            self.db.query(ProductModel)
            .filter(ProductModel.id == product_id)
            .first()
        )
        if not model:
            return False
        self.db.delete(model)
        self.db.commit()
        return True

    def product_exists(self, product_id: int) -> bool:
        return self.get_by_id(product_id) is not None
