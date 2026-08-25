from decimal import Decimal


def build_product_group_key(
    *,
    nome: str,
    clube: str,
    category_id: int,
    tipo: str,
    imagem_url: str | None,
    preco: Decimal | float | str,
) -> str:
    return "|".join(
        [
            nome.strip().lower(),
            clube.strip().lower(),
            str(category_id),
            tipo.strip().lower(),
            imagem_url or "",
            str(preco),
        ]
    )
