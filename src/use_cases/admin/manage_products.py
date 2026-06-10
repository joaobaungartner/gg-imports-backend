from src.entities.admin import AdminEntity
from src.repositories.admin_repository import AdminRepository


class ManageProductsUseCase:
    def __init__(self, admin_repository: AdminRepository):
        self.admin_repository = admin_repository
        # TODO: injetar ProductRepository quando disponível

    def validate_admin_permission(self, admin_id: int) -> AdminEntity:
        admin = self.admin_repository.get_by_id(admin_id)
        if not admin:
            raise ValueError("Admin não encontrado")
        if not admin.has_admin_permission():
            raise ValueError("Permissão negada")
        return admin

    def cadastrar_produto(self, admin_id: int) -> None:
        admin = self.validate_admin_permission(admin_id)
        admin.cadastrar_produto()

        # TODO: integrar com ProductRepository para cadastrar produto
        # Exemplo futuro:
        # return self.product_repository.create(produto_data)

    def editar_produto(self, admin_id: int, produto_id: int) -> None:
        admin = self.validate_admin_permission(admin_id)
        admin.editar_produto(produto_id)

        # TODO: integrar com ProductRepository para editar produto
        # Exemplo futuro:
        # return self.product_repository.update(produto_id, produto_data)

    def remover_produto(self, admin_id: int, produto_id: int) -> None:
        admin = self.validate_admin_permission(admin_id)
        admin.remover_produto(produto_id)

        # TODO: integrar com ProductRepository para remover produto
        # Exemplo futuro:
        # return self.product_repository.delete(produto_id)
