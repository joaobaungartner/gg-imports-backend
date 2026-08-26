from datetime import datetime
from sqlalchemy.orm import Session
from src.models.post_sale_request_model import PostSaleRequestModel


class PostSaleRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, order_id: int, client_id: int, request_type: str, reason: str):
        model = PostSaleRequestModel(
            order_id=order_id, client_id=client_id,
            request_type=request_type, reason=reason,
            status="REQUESTED", created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def get(self, request_id: int):
        return self.db.query(PostSaleRequestModel).filter_by(id=request_id).first()

    def list_for_client(self, client_id: int):
        return self.db.query(PostSaleRequestModel).filter_by(client_id=client_id).order_by(PostSaleRequestModel.created_at.desc()).all()

    def list_all(self):
        return self.db.query(PostSaleRequestModel).order_by(PostSaleRequestModel.created_at.desc()).all()

    def update(self, request_id: int, status: str, admin_note: str | None):
        model = self.get(request_id)
        if not model:
            return None
        model.status = status
        model.admin_note = admin_note
        model.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(model)
        return model
