from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session, joinedload

from src.entities.order import OrderEntity, OrderStatus
from src.entities.order_item import OrderItemEntity
from src.models.order_item_model import OrderItemModel
from src.models.order_model import OrderModel


class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def _item_to_entity(self, model: OrderItemModel) -> OrderItemEntity:
        return OrderItemEntity(
            id=model.id,
            order_id=model.order_id,
            product_id=model.product_id,
            quantidade=model.quantidade,
            preco_unitario=Decimal(str(model.preco_unitario)),
            ativo=model.ativo,
        )

    def _item_to_model(self, entity: OrderItemEntity, order_id: int) -> OrderItemModel:
        kwargs = {
            "order_id": order_id,
            "product_id": entity.product_id,
            "quantidade": entity.quantidade,
            "preco_unitario": entity.preco_unitario,
            "ativo": entity.ativo,
        }
        if entity.id is not None:
            kwargs["id"] = entity.id
        return OrderItemModel(**kwargs)

    def _to_entity(self, model: OrderModel) -> OrderEntity:
        itens = [self._item_to_entity(item) for item in model.itens]
        return OrderEntity(
            id=model.id,
            client_id=model.client_id,
            endereco_id=model.endereco_id,
            data_pedido=model.data_pedido,
            valor_total=Decimal(str(model.valor_total)),
            status=OrderStatus(model.status),
            pagamento_id=model.pagamento_id,
            cupom_id=model.cupom_id,
            desconto_cupom=Decimal(str(model.desconto_cupom)),
            ativo=model.ativo,
            itens=itens,
        )

    def _to_model(self, entity: OrderEntity) -> OrderModel:
        kwargs = {
            "client_id": entity.client_id,
            "endereco_id": entity.endereco_id,
            "data_pedido": entity.data_pedido or datetime.utcnow(),
            "valor_total": entity.valor_total,
            "desconto_cupom": entity.desconto_cupom,
            "status": entity.status.value,
            "pagamento_id": entity.pagamento_id,
            "cupom_id": entity.cupom_id,
            "ativo": entity.ativo,
        }
        if entity.id is not None:
            kwargs["id"] = entity.id
        return OrderModel(**kwargs)

    def _load_order(self, order_id: int) -> OrderModel | None:
        return (
            self.db.query(OrderModel)
            .options(joinedload(OrderModel.itens))
            .filter(OrderModel.id == order_id)
            .first()
        )

    def create(self, order: OrderEntity) -> OrderEntity:
        model = self._to_model(order)
        self.db.add(model)
        self.db.flush()

        for item in order.itens:
            item_model = self._item_to_model(item, model.id)
            self.db.add(item_model)

        self.db.commit()
        return self._to_entity(self._load_order(model.id))

    def get_by_id(self, order_id: int) -> OrderEntity | None:
        model = self._load_order(order_id)
        if not model:
            return None
        return self._to_entity(model)

    def get_by_client_id(self, client_id: int) -> list[OrderEntity]:
        models = (
            self.db.query(OrderModel)
            .options(joinedload(OrderModel.itens))
            .filter(OrderModel.client_id == client_id)
            .all()
        )
        return [self._to_entity(model) for model in models]

    def list_all(self) -> list[OrderEntity]:
        models = (
            self.db.query(OrderModel)
            .options(joinedload(OrderModel.itens))
            .all()
        )
        return [self._to_entity(model) for model in models]

    def list_by_status(self, status: str) -> list[OrderEntity]:
        models = (
            self.db.query(OrderModel)
            .options(joinedload(OrderModel.itens))
            .filter(OrderModel.status == status)
            .all()
        )
        return [self._to_entity(model) for model in models]

    def update(self, order_id: int, data: dict) -> OrderEntity | None:
        model = self._load_order(order_id)
        if not model:
            return None
        for key, value in data.items():
            if hasattr(model, key):
                setattr(model, key, value)
        self.db.commit()
        return self._to_entity(self._load_order(order_id))

    def update_status(self, order_id: int, status: str) -> OrderEntity | None:
        return self.update(order_id, {"status": status})

    def deactivate(self, order_id: int) -> OrderEntity | None:
        return self.update(order_id, {"ativo": False})

    def delete(self, order_id: int) -> bool:
        model = self.db.query(OrderModel).filter(OrderModel.id == order_id).first()
        if not model:
            return False
        self.db.delete(model)
        self.db.commit()
        return True

    def add_item(self, order_id: int, item: OrderItemEntity) -> OrderEntity | None:
        model = self._load_order(order_id)
        if not model:
            return None
        item_model = self._item_to_model(item, order_id)
        self.db.add(item_model)
        self.db.commit()
        return self._to_entity(self._load_order(order_id))

    def remove_item(self, order_id: int, item_id: int) -> OrderEntity | None:
        model = self._load_order(order_id)
        if not model:
            return None
        item_model = (
            self.db.query(OrderItemModel)
            .filter(
                OrderItemModel.id == item_id,
                OrderItemModel.order_id == order_id,
            )
            .first()
        )
        if not item_model:
            return None
        self.db.delete(item_model)
        self.db.commit()
        return self._to_entity(self._load_order(order_id))
