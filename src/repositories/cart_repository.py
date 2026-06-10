from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session, joinedload

from src.entities.cart import CartEntity
from src.entities.cart_item import CartItemEntity
from src.models.cart_item_model import CartItemModel
from src.models.cart_model import CartModel


class CartRepository:
    def __init__(self, db: Session):
        self.db = db

    def _item_to_entity(self, model: CartItemModel) -> CartItemEntity:
        return CartItemEntity(
            id=model.id,
            cart_id=model.cart_id,
            product_id=model.product_id,
            quantidade=model.quantidade,
            preco_unitario=Decimal(str(model.preco_unitario)),
            ativo=model.ativo,
        )

    def _item_to_model(self, entity: CartItemEntity, cart_id: int) -> CartItemModel:
        kwargs = {
            "cart_id": cart_id,
            "product_id": entity.product_id,
            "quantidade": entity.quantidade,
            "preco_unitario": entity.preco_unitario,
            "ativo": entity.ativo,
        }
        if entity.id is not None:
            kwargs["id"] = entity.id
        return CartItemModel(**kwargs)

    def _to_entity(self, model: CartModel) -> CartEntity:
        itens = [self._item_to_entity(item) for item in model.itens]
        return CartEntity(
            id=model.id,
            client_id=model.client_id,
            data_criacao=model.data_criacao,
            ativo=model.ativo,
            itens=itens,
        )

    def _to_model(self, entity: CartEntity) -> CartModel:
        kwargs = {
            "client_id": entity.client_id,
            "data_criacao": entity.data_criacao or datetime.utcnow(),
            "ativo": entity.ativo,
        }
        if entity.id is not None:
            kwargs["id"] = entity.id
        return CartModel(**kwargs)

    def _load_cart(self, cart_id: int) -> CartModel | None:
        return (
            self.db.query(CartModel)
            .options(joinedload(CartModel.itens))
            .filter(CartModel.id == cart_id)
            .first()
        )

    def create(self, cart: CartEntity) -> CartEntity:
        model = self._to_model(cart)
        self.db.add(model)
        self.db.flush()

        for item in cart.itens:
            item_model = self._item_to_model(item, model.id)
            self.db.add(item_model)

        self.db.commit()
        return self._to_entity(self._load_cart(model.id))

    def get_by_id(self, cart_id: int) -> CartEntity | None:
        model = self._load_cart(cart_id)
        if not model:
            return None
        return self._to_entity(model)

    def get_by_client_id(self, client_id: int) -> CartEntity | None:
        model = (
            self.db.query(CartModel)
            .options(joinedload(CartModel.itens))
            .filter(
                CartModel.client_id == client_id,
                CartModel.ativo.is_(True),
            )
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def list_all(self) -> list[CartEntity]:
        models = (
            self.db.query(CartModel)
            .options(joinedload(CartModel.itens))
            .all()
        )
        return [self._to_entity(model) for model in models]

    def update(self, cart_id: int, data: dict) -> CartEntity | None:
        model = self._load_cart(cart_id)
        if not model:
            return None
        for key, value in data.items():
            if hasattr(model, key):
                setattr(model, key, value)
        self.db.commit()
        return self._to_entity(self._load_cart(cart_id))

    def deactivate(self, cart_id: int) -> CartEntity | None:
        model = self._load_cart(cart_id)
        if not model:
            return None
        model.ativo = False
        for item in model.itens:
            item.ativo = False
        self.db.commit()
        return self._to_entity(self._load_cart(cart_id))

    def clear_cart(self, cart_id: int) -> CartEntity | None:
        model = self._load_cart(cart_id)
        if not model:
            return None
        for item in model.itens:
            if item.ativo:
                item.ativo = False
        self.db.commit()
        return self._to_entity(self._load_cart(cart_id))

    def cart_exists_for_client(self, client_id: int) -> bool:
        return (
            self.db.query(CartModel)
            .filter(
                CartModel.client_id == client_id,
                CartModel.ativo.is_(True),
            )
            .first()
            is not None
        )
