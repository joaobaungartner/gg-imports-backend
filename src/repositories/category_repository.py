from sqlalchemy.orm import Session

from src.entities.category import CategoryEntity
from src.models.category_model import CategoryModel


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def _normalize_nome(self, nome: str) -> str:
        return nome.strip()

    def _to_entity(self, model: CategoryModel) -> CategoryEntity:
        return CategoryEntity(
            id=model.id,
            nome=model.nome,
            descricao=model.descricao,
            ativo=model.ativo,
        )

    def _to_model(self, entity: CategoryEntity) -> CategoryModel:
        kwargs = {
            "nome": self._normalize_nome(entity.nome),
            "descricao": entity.descricao,
            "ativo": entity.ativo,
        }
        if entity.id is not None:
            kwargs["id"] = entity.id
        return CategoryModel(**kwargs)

    def create(self, category: CategoryEntity) -> CategoryEntity:
        model = self._to_model(category)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def get_by_id(self, category_id: int) -> CategoryEntity | None:
        model = (
            self.db.query(CategoryModel)
            .filter(CategoryModel.id == category_id)
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def get_by_name(self, nome: str) -> CategoryEntity | None:
        nome_normalizado = self._normalize_nome(nome)
        model = (
            self.db.query(CategoryModel)
            .filter(CategoryModel.nome == nome_normalizado)
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def list_all(self) -> list[CategoryEntity]:
        models = self.db.query(CategoryModel).all()
        return [self._to_entity(model) for model in models]

    def list_active(self) -> list[CategoryEntity]:
        models = (
            self.db.query(CategoryModel)
            .filter(CategoryModel.ativo.is_(True))
            .all()
        )
        return [self._to_entity(model) for model in models]

    def update(self, category_id: int, data: dict) -> CategoryEntity | None:
        model = (
            self.db.query(CategoryModel)
            .filter(CategoryModel.id == category_id)
            .first()
        )
        if not model:
            return None
        if "nome" in data:
            data["nome"] = self._normalize_nome(data["nome"])
        if "descricao" in data and data["descricao"] is not None:
            data["descricao"] = data["descricao"].strip() or None
        for key, value in data.items():
            if hasattr(model, key):
                setattr(model, key, value)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def activate(self, category_id: int) -> CategoryEntity | None:
        return self.update(category_id, {"ativo": True})

    def deactivate(self, category_id: int) -> CategoryEntity | None:
        return self.update(category_id, {"ativo": False})

    def delete(self, category_id: int) -> bool:
        model = (
            self.db.query(CategoryModel)
            .filter(CategoryModel.id == category_id)
            .first()
        )
        if not model:
            return False
        self.db.delete(model)
        self.db.commit()
        return True

    def name_exists(self, nome: str) -> bool:
        nome_normalizado = self._normalize_nome(nome)
        return (
            self.db.query(CategoryModel)
            .filter(CategoryModel.nome == nome_normalizado)
            .first()
            is not None
        )
