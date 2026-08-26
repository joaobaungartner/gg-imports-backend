import csv
import io
import json
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.entities.user import UserEntity
from src.middlewares.auth import get_current_admin
from src.models.admin_audit_log_model import AdminAuditLogModel
from src.models.client_model import ClientModel
from src.models.order_item_model import OrderItemModel
from src.models.order_model import OrderModel
from src.models.product_model import ProductModel
from src.models.stock_movement_model import StockMovementModel
from src.models.user_model import UserModel

router = APIRouter(prefix="/admin/management", tags=["Admin Management"])
SALE_STATUSES = ("PAID", "PROCESSING", "SHIPPED", "DELIVERED")


class StockAdjustment(BaseModel):
    quantity_delta: int
    reason: str = Field(..., min_length=3, max_length=500)

    @field_validator("quantity_delta")
    @classmethod
    def non_zero_delta(cls, value: int) -> int:
        if value == 0:
            raise ValueError("O ajuste não pode ser zero")
        return value


class ClientStatusUpdate(BaseModel):
    active: bool


def audit(db: Session, user_id: int, action: str, resource_type: str,
          resource_id: str | int | None = None, details: dict | None = None) -> None:
    db.add(AdminAuditLogModel(
        admin_user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        details=json.dumps(details, ensure_ascii=False, default=str) if details else None,
    ))


@router.get("/reports/sales")
def sales_report(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    filters = [OrderModel.ativo.is_(True), OrderModel.status.in_(SALE_STATUSES)]
    if date_from:
        filters.append(OrderModel.data_pedido >= date_from)
    if date_to:
        filters.append(OrderModel.data_pedido <= date_to)
    total, count = db.query(
        func.coalesce(func.sum(OrderModel.valor_total), 0), func.count(OrderModel.id)
    ).filter(*filters).one()
    top = (
        db.query(
            OrderItemModel.product_id,
            OrderItemModel.nome_produto,
            func.sum(OrderItemModel.quantidade).label("quantity"),
            func.sum(OrderItemModel.quantidade * OrderItemModel.preco_unitario).label("revenue"),
        )
        .join(OrderModel, OrderModel.id == OrderItemModel.order_id)
        .filter(*filters, OrderItemModel.ativo.is_(True))
        .group_by(OrderItemModel.product_id, OrderItemModel.nome_produto)
        .order_by(desc("quantity"))
        .limit(10).all()
    )
    total = Decimal(total or 0)
    return {
        "revenue": str(total), "order_count": count,
        "average_ticket": str(total / count if count else Decimal("0")),
        "top_products": [
            {"product_id": row.product_id, "name": row.nome_produto,
             "quantity": int(row.quantity), "revenue": str(row.revenue or 0)} for row in top
        ],
    }


@router.get("/orders/export.csv")
def export_orders(
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    rows = db.query(OrderModel).filter(OrderModel.ativo.is_(True)).order_by(OrderModel.id.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["pedido", "data", "cliente", "email", "status", "pagamento", "total", "rastreio"])
    for order in rows:
        writer.writerow([
            order.id, order.data_pedido.isoformat(), order.customer_name or "",
            order.customer_email or "", order.status, order.payment_method or "",
            str(order.valor_total), order.codigo_rastreio or "",
        ])
    audit(db, current_user.id, "EXPORT", "orders", details={"count": len(rows)})
    db.commit()
    content = "\ufeff" + output.getvalue()
    return StreamingResponse(
        iter([content]), media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=pedidos.csv"},
    )


@router.get("/stock/low")
def low_stock(
    threshold: int = Query(5, ge=0, le=10000),
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    products = db.query(ProductModel).filter(
        ProductModel.ativo.is_(True), ProductModel.estoque <= threshold
    ).order_by(ProductModel.estoque, ProductModel.nome).all()
    return [{"id": p.id, "name": p.nome, "sku": p.sku, "size": p.tamanho,
             "stock": p.estoque, "image_url": p.imagem_url} for p in products]


@router.get("/stock/movements")
def stock_movements(
    product_id: int | None = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    query = db.query(StockMovementModel, ProductModel.nome).join(ProductModel)
    if product_id:
        query = query.filter(StockMovementModel.product_id == product_id)
    rows = query.order_by(StockMovementModel.created_at.desc()).limit(limit).all()
    return [{"id": m.id, "product_id": m.product_id, "product_name": name,
             "type": m.movement_type, "quantity": m.quantity,
             "previous_stock": m.previous_stock, "new_stock": m.new_stock,
             "reason": m.reason, "order_id": m.order_id,
             "changed_by_user_id": m.changed_by_user_id,
             "created_at": m.created_at} for m, name in rows]


@router.post("/stock/{product_id}/adjust")
def adjust_stock(
    product_id: int,
    payload: StockAdjustment,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    product = db.query(ProductModel).filter(ProductModel.id == product_id).with_for_update().first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    previous = product.estoque
    new_stock = previous + payload.quantity_delta
    if new_stock < 0:
        raise HTTPException(status_code=409, detail="Ajuste deixaria o estoque negativo")
    product.estoque = new_stock
    db.add(StockMovementModel(
        product_id=product.id, movement_type="ADMIN_ADJUSTMENT",
        quantity=payload.quantity_delta, previous_stock=previous, new_stock=new_stock,
        reason=payload.reason, changed_by_user_id=current_user.id,
    ))
    audit(db, current_user.id, "STOCK_ADJUST", "product", product.id,
          {"delta": payload.quantity_delta, "before": previous, "after": new_stock,
           "reason": payload.reason})
    db.commit()
    return {"product_id": product.id, "previous_stock": previous, "new_stock": new_stock}


@router.get("/clients")
def list_clients(
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    query = db.query(
        ClientModel, UserModel,
        func.count(OrderModel.id).label("order_count"),
        func.coalesce(func.sum(OrderModel.valor_total), 0).label("total_spent"),
    ).join(UserModel, UserModel.id == ClientModel.user_id).outerjoin(
        OrderModel, (OrderModel.client_id == ClientModel.id) & OrderModel.status.in_(SALE_STATUSES)
    )
    if search:
        term = f"%{search}%"
        query = query.filter((UserModel.nome.ilike(term)) | (UserModel.email.ilike(term)) | (ClientModel.cpf.ilike(term)))
    rows = query.group_by(ClientModel.id, UserModel.id).order_by(UserModel.nome).all()
    return [{"id": c.id, "user_id": u.id, "name": u.nome, "email": u.email,
             "phone": u.telefone, "cpf": c.cpf, "active": bool(c.ativo and u.ativo),
             "email_verified": u.email_verificado, "order_count": count,
             "total_spent": str(total)} for c, u, count, total in rows]


@router.patch("/clients/{client_id}/status")
def update_client_status(
    client_id: int,
    payload: ClientStatusUpdate,
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    client = db.query(ClientModel).filter(ClientModel.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    client.ativo = payload.active
    client.user.ativo = payload.active
    audit(db, current_user.id, "CLIENT_STATUS", "client", client_id, {"active": payload.active})
    db.commit()
    return {"id": client.id, "active": payload.active}


@router.get("/audit")
def audit_log(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: UserEntity = Depends(get_current_admin),
):
    rows = db.query(AdminAuditLogModel, UserModel.nome).join(
        UserModel, UserModel.id == AdminAuditLogModel.admin_user_id
    ).order_by(AdminAuditLogModel.created_at.desc()).limit(limit).all()
    return [{"id": log.id, "admin_user_id": log.admin_user_id, "admin_name": name,
             "action": log.action, "resource_type": log.resource_type,
             "resource_id": log.resource_id, "details": json.loads(log.details) if log.details else None,
             "created_at": log.created_at} for log, name in rows]
