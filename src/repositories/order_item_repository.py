from decimal import Decimal

from sqlalchemy.orm import Session

from src.entities.order_item import OrderItemEntity
from src.models.order_item_model import OrderItemModel


class OrderItemRepository:
    def __init__(self, db: Session):
        self.db = db

    def _to_entity(self, model: OrderItemModel) -> OrderItemEntity:
        return OrderItemEntity(
            id=model.id,
            order_id=model.order_id,
            product_id=model.product_id,
            quantidade=model.quantidade,
            preco_unitario=Decimal(str(model.preco_unitario)),
            ativo=model.ativo,
        )

    def _to_model(self, entity: OrderItemEntity) -> OrderItemModel:
        kwargs = {
            "order_id": entity.order_id,
            "product_id": entity.product_id,
            "quantidade": entity.quantidade,
            "preco_unitario": entity.preco_unitario,
            "ativo": entity.ativo,
        }
        if entity.id is not None:
            kwargs["id"] = entity.id
        return OrderItemModel(**kwargs)

    def create(self, order_item: OrderItemEntity) -> OrderItemEntity:
        if order_item.order_id is None:
            raise ValueError("Pedido não encontrado")
        model = self._to_model(order_item)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def get_by_id(self, order_item_id: int) -> OrderItemEntity | None:
        model = (
            self.db.query(OrderItemModel)
            .filter(OrderItemModel.id == order_item_id)
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def get_by_order_id(self, order_id: int) -> list[OrderItemEntity]:
        models = (
            self.db.query(OrderItemModel)
            .filter(OrderItemModel.order_id == order_id)
            .all()
        )
        return [self._to_entity(model) for model in models]

    def get_by_product_id(self, product_id: int) -> list[OrderItemEntity]:
        models = (
            self.db.query(OrderItemModel)
            .filter(OrderItemModel.product_id == product_id)
            .all()
        )
        return [self._to_entity(model) for model in models]

    def get_by_order_and_product(
        self, order_id: int, product_id: int
    ) -> OrderItemEntity | None:
        model = (
            self.db.query(OrderItemModel)
            .filter(
                OrderItemModel.order_id == order_id,
                OrderItemModel.product_id == product_id,
                OrderItemModel.ativo.is_(True),
            )
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def list_all(self) -> list[OrderItemEntity]:
        models = self.db.query(OrderItemModel).all()
        return [self._to_entity(model) for model in models]

    def update(self, order_item_id: int, data: dict) -> OrderItemEntity | None:
        model = (
            self.db.query(OrderItemModel)
            .filter(OrderItemModel.id == order_item_id)
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

    def update_quantity(
        self, order_item_id: int, quantidade: int
    ) -> OrderItemEntity | None:
        return self.update(order_item_id, {"quantidade": quantidade})

    def deactivate(self, order_item_id: int) -> OrderItemEntity | None:
        return self.update(order_item_id, {"ativo": False})

    def delete(self, order_item_id: int) -> bool:
        model = (
            self.db.query(OrderItemModel)
            .filter(OrderItemModel.id == order_item_id)
            .first()
        )
        if not model:
            return False
        self.db.delete(model)
        self.db.commit()
        return True

    def delete_by_order_id(self, order_id: int) -> int:
        count = (
            self.db.query(OrderItemModel)
            .filter(OrderItemModel.order_id == order_id)
            .delete()
        )
        self.db.commit()
        return count
