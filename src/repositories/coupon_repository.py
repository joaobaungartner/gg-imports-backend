from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from src.entities.coupon import CouponEntity
from src.models.coupon_model import CouponModel


class CouponRepository:
    def __init__(self, db: Session):
        self.db = db

    def _normalize_codigo(self, codigo: str) -> str:
        return codigo.strip().upper()

    def _to_entity(self, model: CouponModel) -> CouponEntity:
        return CouponEntity(
            id=model.id,
            codigo=model.codigo,
            desconto=Decimal(str(model.desconto)),
            validade=model.validade,
            ativo=model.ativo,
        )

    def _to_model(self, entity: CouponEntity) -> CouponModel:
        validade = entity.validade
        if isinstance(validade, datetime):
            validade = validade.date()

        kwargs = {
            "codigo": self._normalize_codigo(entity.codigo),
            "desconto": entity.desconto,
            "validade": validade,
            "ativo": entity.ativo,
        }
        if entity.id is not None:
            kwargs["id"] = entity.id
        return CouponModel(**kwargs)

    def create(self, coupon: CouponEntity) -> CouponEntity:
        model = self._to_model(coupon)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def get_by_id(self, coupon_id: int) -> CouponEntity | None:
        model = (
            self.db.query(CouponModel).filter(CouponModel.id == coupon_id).first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def get_by_code(self, codigo: str) -> CouponEntity | None:
        codigo_normalizado = self._normalize_codigo(codigo)
        model = (
            self.db.query(CouponModel)
            .filter(CouponModel.codigo == codigo_normalizado)
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def list_all(self) -> list[CouponEntity]:
        models = self.db.query(CouponModel).all()
        return [self._to_entity(model) for model in models]

    def list_active(self) -> list[CouponEntity]:
        models = (
            self.db.query(CouponModel).filter(CouponModel.ativo.is_(True)).all()
        )
        return [self._to_entity(model) for model in models]

    def list_expired(self) -> list[CouponEntity]:
        hoje = date.today()
        models = (
            self.db.query(CouponModel)
            .filter(CouponModel.validade < hoje)
            .all()
        )
        return [self._to_entity(model) for model in models]

    def update(self, coupon_id: int, data: dict) -> CouponEntity | None:
        model = (
            self.db.query(CouponModel).filter(CouponModel.id == coupon_id).first()
        )
        if not model:
            return None
        if "codigo" in data:
            data["codigo"] = self._normalize_codigo(data["codigo"])
        for key, value in data.items():
            if hasattr(model, key):
                setattr(model, key, value)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def activate(self, coupon_id: int) -> CouponEntity | None:
        return self.update(coupon_id, {"ativo": True})

    def deactivate(self, coupon_id: int) -> CouponEntity | None:
        return self.update(coupon_id, {"ativo": False})

    def delete(self, coupon_id: int) -> bool:
        model = (
            self.db.query(CouponModel).filter(CouponModel.id == coupon_id).first()
        )
        if not model:
            return False
        self.db.delete(model)
        self.db.commit()
        return True

    def code_exists(self, codigo: str) -> bool:
        codigo_normalizado = self._normalize_codigo(codigo)
        return (
            self.db.query(CouponModel)
            .filter(CouponModel.codigo == codigo_normalizado)
            .first()
            is not None
        )
