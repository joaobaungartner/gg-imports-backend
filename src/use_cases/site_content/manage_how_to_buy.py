from src.repositories.site_content_repository import SiteContentRepository


class GetHowToBuyContentUseCase:
    def __init__(self, site_content_repository: SiteContentRepository):
        self.site_content_repository = site_content_repository

    def execute(self) -> dict:
        return self.site_content_repository.get_how_to_buy()


class UpdateHowToBuyContentUseCase:
    def __init__(self, site_content_repository: SiteContentRepository):
        self.site_content_repository = site_content_repository

    def execute(self, payload: dict) -> dict:
        title = (payload.get("title") or "").strip()
        subtitle = (payload.get("subtitle") or "").strip()
        eyebrow = (payload.get("eyebrow") or "Passo a passo").strip()
        steps_raw = payload.get("steps") or []

        if not title:
            raise ValueError("Título é obrigatório")
        if not subtitle:
            raise ValueError("Introdução é obrigatória")
        if not isinstance(steps_raw, list) or len(steps_raw) < 1:
            raise ValueError("Informe ao menos uma etapa")
        if len(steps_raw) > 20:
            raise ValueError("Limite de 20 etapas excedido")

        steps = []
        for index, step in enumerate(steps_raw, start=1):
            step_title = (step.get("title") or "").strip()
            step_description = (step.get("description") or "").strip()
            if not step_title:
                raise ValueError(f"Título da etapa {index} é obrigatório")
            if not step_description:
                raise ValueError(f"Descrição da etapa {index} é obrigatória")
            if len(step_title) > 120 or len(step_description) > 1000:
                raise ValueError("Etapa excede o limite de caracteres")
            steps.append(
                {
                    "title": step_title,
                    "description": step_description,
                }
            )

        cleaned = {
            "title": title[:120],
            "subtitle": subtitle[:500],
            "eyebrow": eyebrow[:80],
            "steps": steps,
        }
        return self.site_content_repository.upsert("how_to_buy", cleaned)
