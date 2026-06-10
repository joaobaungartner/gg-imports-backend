from datetime import datetime

from sqlalchemy.orm import Session

from src.entities.user import UserEntity, UserRole
from src.models.user_model import UserModel


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def _to_entity(self, model: UserModel) -> UserEntity:
        return UserEntity(
            id=model.id,
            nome=model.nome,
            email=model.email,
            senha_hash=model.senha_hash,
            telefone=model.telefone,
            data_cadastro=model.data_cadastro,
            role=UserRole(model.role),
            ativo=model.ativo,
        )

    def _to_model(self, entity: UserEntity) -> UserModel:
        kwargs = {
            "nome": entity.nome,
            "email": entity.email,
            "senha_hash": entity.senha_hash,
            "telefone": entity.telefone,
            "data_cadastro": entity.data_cadastro or datetime.utcnow(),
            "role": entity.role.value,
            "ativo": entity.ativo,
        }
        if entity.id is not None:
            kwargs["id"] = entity.id
        return UserModel(**kwargs)

    def create(self, user: UserEntity) -> UserEntity:
        model = self._to_model(user)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def get_by_id(self, user_id: int) -> UserEntity | None:
        model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not model:
            return None
        return self._to_entity(model)

    def get_by_email(self, email: str) -> UserEntity | None:
        model = self.db.query(UserModel).filter(UserModel.email == email).first()
        if not model:
            return None
        return self._to_entity(model)

    def list_all(self) -> list[UserEntity]:
        models = self.db.query(UserModel).all()
        return [self._to_entity(model) for model in models]

    def update(self, user_id: int, data: dict) -> UserEntity | None:
        model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not model:
            return None
        for key, value in data.items():
            if hasattr(model, key):
                setattr(model, key, value)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def deactivate(self, user_id: int) -> UserEntity | None:
        return self.update(user_id, {"ativo": False})

    def delete(self, user_id: int) -> bool:
        model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not model:
            return False
        self.db.delete(model)
        self.db.commit()
        return True

    def email_exists(self, email: str) -> bool:
        return (
            self.db.query(UserModel).filter(UserModel.email == email).first()
            is not None
        )
