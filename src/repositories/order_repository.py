from datetime import date, datetime
from decimal import Decimal
from math import ceil

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from src.entities.order import OrderEntity, OrderStatus
from src.entities.order_item import OrderItemEntity
from src.models.order_item_model import OrderItemModel
from src.models.order_model import OrderModel
from src.models.payment_model import PaymentModel


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
            nome_produto=model.nome_produto,
            imagem_url=model.imagem_url,
            tamanho=model.tamanho,
            ativo=model.ativo,
        )

    def _item_to_model(self, entity: OrderItemEntity, order_id: int) -> OrderItemModel:
        kwargs = {
            "order_id": order_id,
            "product_id": entity.product_id,
            "quantidade": entity.quantidade,
            "preco_unitario": entity.preco_unitario,
            "nome_produto": entity.nome_produto,
            "imagem_url": entity.imagem_url,
            "tamanho": entity.tamanho,
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
            customer_name=model.customer_name,
            customer_email=model.customer_email,
            customer_phone=model.customer_phone,
            customer_cpf=model.customer_cpf,
            shipping_cep=model.shipping_cep,
            shipping_street=model.shipping_street,
            shipping_number=model.shipping_number,
            shipping_complement=model.shipping_complement,
            shipping_neighborhood=model.shipping_neighborhood,
            shipping_city=model.shipping_city,
            shipping_state=model.shipping_state,
            shipping_method=model.shipping_method,
            payment_method=model.payment_method,
            data_pedido=model.data_pedido,
            updated_at=model.updated_at,
            admin_notes=model.admin_notes,
            subtotal=Decimal(str(model.subtotal)),
            frete=Decimal(str(model.frete)),
            valor_total=Decimal(str(model.valor_total)),
            status=OrderStatus(model.status),
            pagamento_id=model.pagamento.id if model.pagamento else None,
            cupom_id=model.cupom_id,
            desconto_cupom=Decimal(str(model.desconto_cupom)),
            ativo=model.ativo,
            itens=itens,
        )

    def _to_model(self, entity: OrderEntity) -> OrderModel:
        now = datetime.utcnow()
        kwargs = {
            "client_id": entity.client_id,
            "endereco_id": entity.endereco_id,
            "customer_name": entity.customer_name,
            "customer_email": entity.customer_email,
            "customer_phone": entity.customer_phone,
            "customer_cpf": entity.customer_cpf,
            "shipping_cep": entity.shipping_cep,
            "shipping_street": entity.shipping_street,
            "shipping_number": entity.shipping_number,
            "shipping_complement": entity.shipping_complement,
            "shipping_neighborhood": entity.shipping_neighborhood,
            "shipping_city": entity.shipping_city,
            "shipping_state": entity.shipping_state,
            "shipping_method": entity.shipping_method,
            "payment_method": entity.payment_method,
            "data_pedido": entity.data_pedido or now,
            "updated_at": entity.updated_at or now,
            "admin_notes": entity.admin_notes,
            "subtotal": entity.subtotal,
            "frete": entity.frete,
            "valor_total": entity.valor_total,
            "desconto_cupom": entity.desconto_cupom,
            "status": entity.status.value,
            "cupom_id": entity.cupom_id,
            "ativo": entity.ativo,
        }
        if entity.id is not None:
            kwargs["id"] = entity.id
        return OrderModel(**kwargs)

    def _load_order(self, order_id: int) -> OrderModel | None:
        return (
            self.db.query(OrderModel)
            .options(
                joinedload(OrderModel.itens),
                joinedload(OrderModel.pagamento),
            )
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

        from src.models.order_status_history_model import OrderStatusHistoryModel

        self.db.add(
            OrderStatusHistoryModel(
                order_id=model.id,
                previous_status=None,
                new_status=model.status,
                changed_by_user_id=None,
                note=None,
                created_at=datetime.utcnow(),
            )
        )

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
            .options(
                joinedload(OrderModel.itens),
                joinedload(OrderModel.pagamento),
            )
            .filter(OrderModel.client_id == client_id)
            .order_by(OrderModel.data_pedido.desc())
            .all()
        )
        return [self._to_entity(model) for model in models]

    def list_all(self) -> list[OrderEntity]:
        models = (
            self.db.query(OrderModel)
            .options(
                joinedload(OrderModel.itens),
                joinedload(OrderModel.pagamento),
            )
            .order_by(OrderModel.data_pedido.desc())
            .all()
        )
        return [self._to_entity(model) for model in models]

    def list_by_status(self, status: str) -> list[OrderEntity]:
        models = (
            self.db.query(OrderModel)
            .options(
                joinedload(OrderModel.itens),
                joinedload(OrderModel.pagamento),
            )
            .filter(OrderModel.status == status)
            .order_by(OrderModel.data_pedido.desc())
            .all()
        )
        return [self._to_entity(model) for model in models]

    def _apply_admin_filters(
        self,
        query,
        *,
        status: str | None = None,
        shipping_method: str | None = None,
        payment_status: str | None = None,
        payment_method: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        search: str | None = None,
    ):
        if status:
            query = query.filter(OrderModel.status == status)
        if shipping_method:
            query = query.filter(OrderModel.shipping_method == shipping_method.upper())
        if payment_method:
            query = query.filter(OrderModel.payment_method == payment_method.upper())
        if payment_status:
            query = query.outerjoin(PaymentModel, PaymentModel.order_id == OrderModel.id)
            if payment_status.upper() == "PENDING_PAYMENT":
                query = query.filter(
                    or_(
                        PaymentModel.id.is_(None),
                        PaymentModel.status == "PENDING",
                    )
                )
            else:
                query = query.filter(PaymentModel.status == payment_status.upper())
        if date_from:
            query = query.filter(
                OrderModel.data_pedido >= datetime.combine(date_from, datetime.min.time())
            )
        if date_to:
            query = query.filter(
                OrderModel.data_pedido
                <= datetime.combine(date_to, datetime.max.time())
            )
        if search:
            term = search.strip()
            if term:
                like = f"%{term}%"
                filters = [
                    OrderModel.customer_name.ilike(like),
                    OrderModel.customer_email.ilike(like),
                    OrderModel.customer_cpf.ilike(like),
                    OrderModel.customer_phone.ilike(like),
                ]
                if term.isdigit():
                    filters.append(OrderModel.id == int(term))
                query = query.filter(or_(*filters))
        return query

    def list_admin_paginated(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        shipping_method: str | None = None,
        payment_status: str | None = None,
        payment_method: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        search: str | None = None,
        sort: str = "desc",
    ) -> dict:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)

        base_query = self.db.query(OrderModel)
        base_query = self._apply_admin_filters(
            base_query,
            status=status,
            shipping_method=shipping_method,
            payment_status=payment_status,
            payment_method=payment_method,
            date_from=date_from,
            date_to=date_to,
            search=search,
        )

        total = base_query.with_entities(func.count(OrderModel.id)).scalar() or 0
        total_pages = ceil(total / page_size) if total else 0

        order_clause = (
            OrderModel.data_pedido.asc()
            if sort == "asc"
            else OrderModel.data_pedido.desc()
        )

        models = (
            base_query.options(
                joinedload(OrderModel.itens),
                joinedload(OrderModel.pagamento),
            )
            .order_by(order_clause)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {
            "items": [
                {
                    "order": self._to_entity(model),
                    "payment_status": (
                        model.pagamento.status if model.pagamento else None
                    ),
                }
                for model in models
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def admin_summary(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> dict:
        query = self.db.query(OrderModel.status, func.count(OrderModel.id))
        if date_from:
            query = query.filter(
                OrderModel.data_pedido >= datetime.combine(date_from, datetime.min.time())
            )
        if date_to:
            query = query.filter(
                OrderModel.data_pedido
                <= datetime.combine(date_to, datetime.max.time())
            )
        rows = query.group_by(OrderModel.status).all()
        counts = {status: count for status, count in rows}

        total = sum(counts.values())
        pending_payment = counts.get(OrderStatus.PENDING_PAYMENT.value, 0)
        preparing = counts.get(OrderStatus.PREPARING.value, 0) + counts.get(
            OrderStatus.PAID.value, 0
        )
        in_transit = counts.get(OrderStatus.SHIPPED.value, 0) + counts.get(
            OrderStatus.READY_FOR_PICKUP.value, 0
        )
        delivered = counts.get(OrderStatus.DELIVERED.value, 0)
        canceled = counts.get(OrderStatus.CANCELED.value, 0)

        return {
            "total": total,
            "pending_payment": pending_payment,
            "preparing": preparing,
            "shipped_or_ready": in_transit,
            "delivered": delivered,
            "canceled": canceled,
        }

    def update(self, order_id: int, data: dict) -> OrderEntity | None:
        model = self._load_order(order_id)
        if not model:
            return None
        for key, value in data.items():
            if hasattr(model, key):
                setattr(model, key, value)
        if "updated_at" not in data:
            model.updated_at = datetime.utcnow()
        self.db.commit()
        return self._to_entity(self._load_order(order_id))

    def update_status(
        self,
        order_id: int,
        status: str,
        *,
        commit: bool = True,
    ) -> OrderEntity | None:
        model = self._load_order(order_id)
        if not model:
            return None
        model.status = status
        model.updated_at = datetime.utcnow()
        if commit:
            self.db.commit()
            return self._to_entity(self._load_order(order_id))
        self.db.flush()
        return self._to_entity(model)

    def update_admin_notes(self, order_id: int, notes: str | None) -> OrderEntity | None:
        return self.update(order_id, {"admin_notes": notes, "updated_at": datetime.utcnow()})

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

    def get_payment_status(self, order_id: int) -> str | None:
        payment = (
            self.db.query(PaymentModel)
            .filter(PaymentModel.order_id == order_id)
            .first()
        )
        if not payment:
            return None
        return payment.status
