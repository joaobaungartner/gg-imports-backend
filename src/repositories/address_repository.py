from sqlalchemy.orm import Session

from src.entities.address import AddressEntity
from src.models.address_model import AddressModel


class AddressRepository:
    def __init__(self, db: Session):
        self.db = db

    def _to_entity(self, model: AddressModel) -> AddressEntity:
        return AddressEntity(
            id=model.id,
            client_id=model.client_id,
            rua=model.rua,
            numero=model.numero,
            bairro=model.bairro,
            cidade=model.cidade,
            estado=model.estado,
            cep=model.cep,
            ativo=model.ativo,
        )

    def _to_model(self, entity: AddressEntity) -> AddressModel:
        kwargs = {
            "client_id": entity.client_id,
            "rua": entity.rua,
            "numero": entity.numero,
            "bairro": entity.bairro,
            "cidade": entity.cidade,
            "estado": entity.estado,
            "cep": entity.cep,
            "ativo": entity.ativo,
        }
        if entity.id is not None:
            kwargs["id"] = entity.id
        return AddressModel(**kwargs)

    def create(self, address: AddressEntity) -> AddressEntity:
        model = self._to_model(address)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def get_by_id(self, address_id: int) -> AddressEntity | None:
        model = (
            self.db.query(AddressModel).filter(AddressModel.id == address_id).first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def get_by_client_id(self, client_id: int) -> list[AddressEntity]:
        models = (
            self.db.query(AddressModel)
            .filter(AddressModel.client_id == client_id)
            .all()
        )
        return [self._to_entity(model) for model in models]

    def list_all(self) -> list[AddressEntity]:
        models = self.db.query(AddressModel).all()
        return [self._to_entity(model) for model in models]

    def list_active(self) -> list[AddressEntity]:
        models = (
            self.db.query(AddressModel).filter(AddressModel.ativo.is_(True)).all()
        )
        return [self._to_entity(model) for model in models]

    def update(self, address_id: int, data: dict) -> AddressEntity | None:
        model = (
            self.db.query(AddressModel).filter(AddressModel.id == address_id).first()
        )
        if not model:
            return None
        for key, value in data.items():
            if hasattr(model, key):
                setattr(model, key, value)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def deactivate(self, address_id: int) -> AddressEntity | None:
        return self.update(address_id, {"ativo": False})

    def delete(self, address_id: int) -> bool:
        model = (
            self.db.query(AddressModel).filter(AddressModel.id == address_id).first()
        )
        if not model:
            return False
        self.db.delete(model)
        self.db.commit()
        return True

    def cep_exists_for_client(self, client_id: int, cep: str) -> bool:
        return (
            self.db.query(AddressModel)
            .filter(
                AddressModel.client_id == client_id,
                AddressModel.cep == cep,
                AddressModel.ativo.is_(True),
            )
            .first()
            is not None
        )

    def address_belongs_to_client(self, address_id: int, client_id: int) -> bool:
        return (
            self.db.query(AddressModel)
            .filter(
                AddressModel.id == address_id,
                AddressModel.client_id == client_id,
            )
            .first()
            is not None
        )
