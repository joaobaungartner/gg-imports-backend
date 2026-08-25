from dataclasses import dataclass
from datetime import datetime


@dataclass
class OrderStatusHistoryEntity:
    id: int | None
    order_id: int
    previous_status: str | None
    new_status: str
    changed_by_user_id: int | None = None
    note: str | None = None
    created_at: datetime | None = None
    changed_by_name: str | None = None
