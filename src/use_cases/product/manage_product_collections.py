from src.repositories.category_repository import CategoryRepository
from src.repositories.product_collection_repository import ProductCollectionRepository
from src.repositories.product_repository import ProductRepository
from src.utils.product_group_key import build_product_group_key


COLLECTION_NAMES = {
    "promotions": "Promoções",
    "launches": "Lançamentos",
}


class GetAdminProductCollectionUseCase:
    def __init__(
        self,
        collection_repository: ProductCollectionRepository,
        product_repository: ProductRepository,
        category_repository: CategoryRepository,
    ):
        self.collection_repository = collection_repository
        self.product_repository = product_repository
        self.category_repository = category_repository

    def execute(self, slug: str) -> dict:
        if slug not in ProductCollectionRepository.VALID_SLUGS:
            raise ValueError("Coleção inválida")

        selected_keys = self.collection_repository.get_group_keys(slug)
        products = self.product_repository.list_all()
        categories = {
            category.id: category.nome
            for category in self.category_repository.list_all()
        }

        groups: dict[str, dict] = {}
        for product in products:
            key = build_product_group_key(
                nome=product.nome,
                clube=product.clube,
                category_id=product.category_id,
                tipo=product.tipo,
                imagem_url=product.imagem_url,
                preco=product.preco,
            )
            if key not in groups:
                groups[key] = {
                    "group_key": key,
                    "selected": key in selected_keys,
                    "nome": product.nome,
                    "clube": product.clube,
                    "categoria": categories.get(product.category_id, "Categoria"),
                    "tipo": product.tipo,
                    "preco": str(product.preco),
                    "estoque_total": 0,
                    "imagem_url": product.imagem_url,
                    "ativo": False,
                    "variant_ids": [],
                }
            groups[key]["estoque_total"] += product.estoque
            groups[key]["variant_ids"].append(product.id)
            if product.ativo:
                groups[key]["ativo"] = True

        items = sorted(
            groups.values(),
            key=lambda item: (not item["selected"], item["nome"].lower()),
        )
        return {
            "slug": slug,
            "name": COLLECTION_NAMES.get(slug, slug),
            "selected_count": sum(1 for item in items if item["selected"]),
            "items": items,
        }


class UpdateAdminProductCollectionUseCase:
    def __init__(
        self,
        collection_repository: ProductCollectionRepository,
        product_repository: ProductRepository,
        category_repository: CategoryRepository,
    ):
        self.collection_repository = collection_repository
        self.get_use_case = GetAdminProductCollectionUseCase(
            collection_repository,
            product_repository,
            category_repository,
        )

    def execute(self, slug: str, group_keys: list[str]) -> dict:
        products = self.get_use_case.product_repository.list_all()
        valid_keys = {
            build_product_group_key(
                nome=product.nome,
                clube=product.clube,
                category_id=product.category_id,
                tipo=product.tipo,
                imagem_url=product.imagem_url,
                preco=product.preco,
            )
            for product in products
        }
        for key in group_keys:
            if key.strip() and key.strip() not in valid_keys:
                raise ValueError(f"Produto não encontrado na coleção: {key}")

        self.collection_repository.replace_group_keys(slug, group_keys)
        return self.get_use_case.execute(slug)
