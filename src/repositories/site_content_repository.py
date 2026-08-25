from datetime import datetime

from sqlalchemy.orm import Session

from src.models.site_content_model import SiteContentModel


DEFAULT_HOW_TO_BUY = {
    "title": "Como comprar",
    "subtitle": "Do clique ao envio: um processo direto, com suporte quando você precisar.",
    "eyebrow": "Passo a passo",
    "steps": [
        {
            "title": "Escolha sua camisa",
            "description": (
                "Navegue pelo catálogo, filtre por categoria e escolha o modelo, "
                "o tipo e o tamanho certos."
            ),
        },
        {
            "title": "Confira medidas",
            "description": (
                "Use a tabela de medidas e compare com uma peça do seu guarda-roupa. "
                "Em dúvida, fale conosco."
            ),
        },
        {
            "title": "Finalize o pedido",
            "description": (
                "Revise o carrinho, informe entrega ou retirada e confirme o pagamento "
                "(incluindo Pix quando aplicável)."
            ),
        },
        {
            "title": "Acompanhe e receba",
            "description": (
                "Guarde o número do pedido. Acompanhe o status na conta ou pela "
                "página de rastreamento."
            ),
        },
    ],
}


class SiteContentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_key(self, key: str) -> dict | None:
        model = (
            self.db.query(SiteContentModel)
            .filter(SiteContentModel.key == key)
            .first()
        )
        if not model:
            return None
        return dict(model.payload)

    def upsert(self, key: str, payload: dict) -> dict:
        model = (
            self.db.query(SiteContentModel)
            .filter(SiteContentModel.key == key)
            .first()
        )
        now = datetime.utcnow()
        if model:
            model.payload = payload
            model.updated_at = now
        else:
            model = SiteContentModel(key=key, payload=payload, updated_at=now)
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return dict(model.payload)

    def get_how_to_buy(self) -> dict:
        payload = self.get_by_key("how_to_buy")
        if payload:
            return payload
        return self.upsert("how_to_buy", DEFAULT_HOW_TO_BUY)
