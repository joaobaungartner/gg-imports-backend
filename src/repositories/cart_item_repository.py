from decimal import Decimal

from sqlalchemy.orm import Session

from src.entities.cart_item import CartItemEntity
from src.models.cart_item_model import CartItemModel


class CartItemRepository:
    def __init__(self, db: Session):
        self.db = db

    def _to_entity(self, model: CartItemModel) -> CartItemEntity:
        return CartItemEntity(
            id=model.id,
            cart_id=model.cart_id,
            product_id=model.product_id,
            quantidade=model.quantidade,
            preco_unitario=Decimal(str(model.preco_unitario)),
            ativo=model.ativo,
        )

    def _to_model(self, entity: CartItemEntity) -> CartItemModel:
        kwargs = {
            "cart_id": entity.cart_id,
            "product_id": entity.product_id,
            "quantidade": entity.quantidade,
            "preco_unitario": entity.preco_unitario,
            "ativo": entity.ativo,
        }
        if entity.id is not None:
            kwargs["id"] = entity.id
        return CartItemModel(**kwargs)

    def create(self, cart_item: CartItemEntity) -> CartItemEntity:
        if cart_item.cart_id is None:
            raise ValueError("Carrinho não encontrado")
        model = self._to_model(cart_item)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def get_by_id(self, cart_item_id: int) -> CartItemEntity | None:
        model = (
            self.db.query(CartItemModel)
            .filter(CartItemModel.id == cart_item_id)
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def get_by_cart_id(self, cart_id: int) -> list[CartItemEntity]:
        models = (
            self.db.query(CartItemModel)
            .filter(CartItemModel.cart_id == cart_id)
            .all()
        )
        return [self._to_entity(model) for model in models]

    def get_by_product_id(self, product_id: int) -> list[CartItemEntity]:
        models = (
            self.db.query(CartItemModel)
            .filter(CartItemModel.product_id == product_id)
            .all()
        )
        return [self._to_entity(model) for model in models]

    def get_by_cart_and_product(
        self, cart_id: int, product_id: int
    ) -> CartItemEntity | None:
        model = (
            self.db.query(CartItemModel)
            .filter(
                CartItemModel.cart_id == cart_id,
                CartItemModel.product_id == product_id,
                CartItemModel.ativo.is_(True),
            )
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def update(self, cart_item_id: int, data: dict) -> CartItemEntity | None:
        model = (
            self.db.query(CartItemModel)
            .filter(CartItemModel.id == cart_item_id)
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
        self, cart_item_id: int, quantidade: int
    ) -> CartItemEntity | None:
        return self.update(cart_item_id, {"quantidade": quantidade})

    def deactivate(self, cart_item_id: int) -> CartItemEntity | None:
        return self.update(cart_item_id, {"ativo": False})

    def delete(self, cart_item_id: int) -> bool:
        model = (
            self.db.query(CartItemModel)
            .filter(CartItemModel.id == cart_item_id)
            .first()
        )
        if not model:
            return False
        self.db.delete(model)
        self.db.commit()
        return True

    def delete_by_cart_id(self, cart_id: int) -> int:
        count = (
            self.db.query(CartItemModel)
            .filter(CartItemModel.cart_id == cart_id)
            .delete()
        )
        self.db.commit()
        return count
