from sqlalchemy.orm import Session, joinedload

from src.entities.admin import AdminEntity
from src.entities.user import UserRole
from src.models.admin_model import AdminModel
from src.models.user_model import UserModel


class AdminRepository:
    def __init__(self, db: Session):
        self.db = db

    def _to_entity(self, model: AdminModel) -> AdminEntity:
        user = model.user
        return AdminEntity(
            id=user.id,
            admin_id=model.id,
            nome=user.nome,
            email=user.email,
            senha_hash=user.senha_hash,
            telefone=user.telefone,
            data_cadastro=user.data_cadastro,
            role=UserRole.ADMIN,
            ativo=user.ativo and model.ativo,
        )

    def _to_model(self, entity: AdminEntity) -> AdminModel:
        kwargs = {
            "user_id": entity.id,
            "ativo": entity.ativo,
        }
        if entity.admin_id is not None:
            kwargs["id"] = entity.admin_id
        return AdminModel(**kwargs)

    def create(self, admin: AdminEntity) -> AdminEntity:
        if admin.id is None:
            raise ValueError("Usuário não encontrado")
        model = AdminModel(
            user_id=admin.id,
            ativo=admin.ativo,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        model = (
            self.db.query(AdminModel)
            .options(joinedload(AdminModel.user))
            .filter(AdminModel.id == model.id)
            .first()
        )
        return self._to_entity(model)

    def get_by_id(self, admin_id: int) -> AdminEntity | None:
        model = (
            self.db.query(AdminModel)
            .options(joinedload(AdminModel.user))
            .filter(AdminModel.id == admin_id)
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def get_by_user_id(self, user_id: int) -> AdminEntity | None:
        model = (
            self.db.query(AdminModel)
            .options(joinedload(AdminModel.user))
            .filter(AdminModel.user_id == user_id)
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def get_by_email(self, email: str) -> AdminEntity | None:
        model = (
            self.db.query(AdminModel)
            .join(UserModel)
            .options(joinedload(AdminModel.user))
            .filter(UserModel.email == email)
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def list_all(self) -> list[AdminEntity]:
        models = (
            self.db.query(AdminModel)
            .options(joinedload(AdminModel.user))
            .all()
        )
        return [self._to_entity(model) for model in models]

    def update(self, admin_id: int, data: dict) -> AdminEntity | None:
        model = (
            self.db.query(AdminModel)
            .options(joinedload(AdminModel.user))
            .filter(AdminModel.id == admin_id)
            .first()
        )
        if not model:
            return None
        for key, value in data.items():
            if hasattr(model, key):
                setattr(model, key, value)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def deactivate(self, admin_id: int) -> AdminEntity | None:
        return self.update(admin_id, {"ativo": False})

    def is_admin(self, user_id: int) -> bool:
        model = (
            self.db.query(AdminModel)
            .options(joinedload(AdminModel.user))
            .filter(AdminModel.user_id == user_id)
            .first()
        )
        if not model:
            return False
        return (
            model.ativo
            and model.user.ativo
            and model.user.role == UserRole.ADMIN.value
        )
