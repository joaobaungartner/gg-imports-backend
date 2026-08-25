from src.entities.order_status_history import OrderStatusHistoryEntity

STATUS_LABELS: dict[str, str] = {
    "PENDING_PAYMENT": "Aguardando pagamento",
    "PAID": "Pagamento confirmado",
    "PREPARING": "Em preparação",
    "SHIPPED": "Enviado",
    "READY_FOR_PICKUP": "Pronto para retirada",
    "DELIVERED": "Entregue",
    "CANCELED": "Cancelado",
}

STATUS_CUSTOMER_MESSAGES: dict[str, str] = {
    "PENDING_PAYMENT": "Recebemos o seu pedido.",
    "PAID": "O pagamento foi confirmado.",
    "PREPARING": "Seu pedido está sendo preparado.",
    "SHIPPED": "Seu pedido foi enviado.",
    "READY_FOR_PICKUP": "Seu pedido está pronto para retirada.",
    "DELIVERED": "Pedido entregue.",
    "CANCELED": "Pedido cancelado.",
}


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status)


def customer_status_message(status: str) -> str:
    return STATUS_CUSTOMER_MESSAGES.get(status, status_label(status))


def to_customer_timeline(history: list[OrderStatusHistoryEntity]) -> list[dict]:
    items = []
    for entry in history:
        items.append(
            {
                "status": entry.new_status,
                "label": status_label(entry.new_status),
                "message": customer_status_message(entry.new_status),
                "created_at": entry.created_at,
            }
        )
    return items
