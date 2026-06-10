from sqlalchemy.orm import Session, joinedload

from src.entities.client import ClientEntity
from src.entities.user import UserRole
from src.models.client_model import ClientModel


class ClientRepository:
    def __init__(self, db: Session):
        self.db = db

    def _to_entity(self, model: ClientModel) -> ClientEntity:
        user = model.user
        return ClientEntity(
            id=user.id,
            client_id=model.id,
            nome=user.nome,
            email=user.email,
            senha_hash=user.senha_hash,
            telefone=user.telefone,
            data_cadastro=user.data_cadastro,
            role=UserRole.CLIENTE,
            ativo=user.ativo and model.ativo,
            cpf=model.cpf,
        )

    def _to_model(self, entity: ClientEntity) -> ClientModel:
        kwargs = {
            "user_id": entity.id,
            "cpf": entity.cpf,
            "ativo": entity.ativo,
        }
        if entity.client_id is not None:
            kwargs["id"] = entity.client_id
        return ClientModel(**kwargs)

    def create(self, client: ClientEntity) -> ClientEntity:
        if client.id is None:
            raise ValueError("Usuário não encontrado")
        model = ClientModel(
            user_id=client.id,
            cpf=client.cpf,
            ativo=client.ativo,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        model = (
            self.db.query(ClientModel)
            .options(joinedload(ClientModel.user))
            .filter(ClientModel.id == model.id)
            .first()
        )
        return self._to_entity(model)

    def get_by_id(self, client_id: int) -> ClientEntity | None:
        model = (
            self.db.query(ClientModel)
            .options(joinedload(ClientModel.user))
            .filter(ClientModel.id == client_id)
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def get_by_user_id(self, user_id: int) -> ClientEntity | None:
        model = (
            self.db.query(ClientModel)
            .options(joinedload(ClientModel.user))
            .filter(ClientModel.user_id == user_id)
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def get_by_cpf(self, cpf: str) -> ClientEntity | None:
        model = (
            self.db.query(ClientModel)
            .options(joinedload(ClientModel.user))
            .filter(ClientModel.cpf == cpf)
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def list_all(self) -> list[ClientEntity]:
        models = (
            self.db.query(ClientModel)
            .options(joinedload(ClientModel.user))
            .all()
        )
        return [self._to_entity(model) for model in models]

    def update(self, client_id: int, data: dict) -> ClientEntity | None:
        model = (
            self.db.query(ClientModel)
            .options(joinedload(ClientModel.user))
            .filter(ClientModel.id == client_id)
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

    def deactivate(self, client_id: int) -> ClientEntity | None:
        return self.update(client_id, {"ativo": False})

    def cpf_exists(self, cpf: str) -> bool:
        return (
            self.db.query(ClientModel).filter(ClientModel.cpf == cpf).first()
            is not None
        )
