from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from src.entities.order_status_history import OrderStatusHistoryEntity
from src.models.order_status_history_model import OrderStatusHistoryModel


class OrderStatusHistoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def _to_entity(self, model: OrderStatusHistoryModel) -> OrderStatusHistoryEntity:
        changed_by_name = None
        if model.changed_by is not None:
            changed_by_name = model.changed_by.nome
        return OrderStatusHistoryEntity(
            id=model.id,
            order_id=model.order_id,
            previous_status=model.previous_status,
            new_status=model.new_status,
            changed_by_user_id=model.changed_by_user_id,
            note=model.note,
            created_at=model.created_at,
            changed_by_name=changed_by_name,
        )

    def create(
        self,
        order_id: int,
        previous_status: str | None,
        new_status: str,
        changed_by_user_id: int | None = None,
        note: str | None = None,
        *,
        commit: bool = False,
    ) -> OrderStatusHistoryEntity:
        model = OrderStatusHistoryModel(
            order_id=order_id,
            previous_status=previous_status,
            new_status=new_status,
            changed_by_user_id=changed_by_user_id,
            note=note,
            created_at=datetime.utcnow(),
        )
        self.db.add(model)
        if commit:
            self.db.commit()
            self.db.refresh(model)
            model = (
                self.db.query(OrderStatusHistoryModel)
                .options(joinedload(OrderStatusHistoryModel.changed_by))
                .filter(OrderStatusHistoryModel.id == model.id)
                .first()
            )
        else:
            self.db.flush()
        return self._to_entity(model)

    def list_by_order_id(self, order_id: int) -> list[OrderStatusHistoryEntity]:
        models = (
            self.db.query(OrderStatusHistoryModel)
            .options(joinedload(OrderStatusHistoryModel.changed_by))
            .filter(OrderStatusHistoryModel.order_id == order_id)
            .order_by(OrderStatusHistoryModel.created_at.desc())
            .all()
        )
        return [self._to_entity(model) for model in models]
