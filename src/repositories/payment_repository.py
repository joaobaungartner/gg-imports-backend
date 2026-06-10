from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from src.entities.payment import PaymentEntity, PaymentMethod, PaymentStatus
from src.models.payment_model import PaymentModel


class PaymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def _to_entity(self, model: PaymentModel) -> PaymentEntity:
        return PaymentEntity(
            id=model.id,
            order_id=model.order_id,
            metodo=PaymentMethod(model.metodo),
            status=PaymentStatus(model.status),
            valor=Decimal(str(model.valor)),
            codigo_transacao=model.codigo_transacao,
            data_pagamento=model.data_pagamento,
            ativo=model.ativo,
        )

    def _to_model(self, entity: PaymentEntity) -> PaymentModel:
        metodo = (
            entity.metodo.value
            if isinstance(entity.metodo, PaymentMethod)
            else entity.metodo
        )
        kwargs = {
            "order_id": entity.order_id,
            "metodo": metodo,
            "status": entity.status.value,
            "valor": entity.valor,
            "codigo_transacao": entity.codigo_transacao,
            "data_pagamento": entity.data_pagamento,
            "ativo": entity.ativo,
        }
        if entity.id is not None:
            kwargs["id"] = entity.id
        return PaymentModel(**kwargs)

    def create(self, payment: PaymentEntity) -> PaymentEntity:
        model = self._to_model(payment)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def get_by_id(self, payment_id: int) -> PaymentEntity | None:
        model = (
            self.db.query(PaymentModel).filter(PaymentModel.id == payment_id).first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def get_by_order_id(self, order_id: int) -> PaymentEntity | None:
        model = (
            self.db.query(PaymentModel)
            .filter(PaymentModel.order_id == order_id)
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def get_by_transaction_code(
        self, codigo_transacao: str
    ) -> PaymentEntity | None:
        model = (
            self.db.query(PaymentModel)
            .filter(PaymentModel.codigo_transacao == codigo_transacao)
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def list_all(self) -> list[PaymentEntity]:
        models = self.db.query(PaymentModel).all()
        return [self._to_entity(model) for model in models]

    def list_by_status(self, status: str) -> list[PaymentEntity]:
        models = (
            self.db.query(PaymentModel)
            .filter(PaymentModel.status == status)
            .all()
        )
        return [self._to_entity(model) for model in models]

    def update(self, payment_id: int, data: dict) -> PaymentEntity | None:
        model = (
            self.db.query(PaymentModel).filter(PaymentModel.id == payment_id).first()
        )
        if not model:
            return None
        for key, value in data.items():
            if hasattr(model, key):
                setattr(model, key, value)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def update_status(self, payment_id: int, status: str) -> PaymentEntity | None:
        return self.update(payment_id, {"status": status})

    def confirm(
        self, payment_id: int, codigo_transacao: str
    ) -> PaymentEntity | None:
        return self.update(
            payment_id,
            {
                "status": PaymentStatus.PAID.value,
                "codigo_transacao": codigo_transacao,
                "data_pagamento": datetime.utcnow(),
            },
        )

    def cancel(self, payment_id: int) -> PaymentEntity | None:
        return self.update(payment_id, {"status": PaymentStatus.CANCELED.value})

    def deactivate(self, payment_id: int) -> PaymentEntity | None:
        return self.update(payment_id, {"ativo": False})

    def delete(self, payment_id: int) -> bool:
        model = (
            self.db.query(PaymentModel).filter(PaymentModel.id == payment_id).first()
        )
        if not model:
            return False
        self.db.delete(model)
        self.db.commit()
        return True
