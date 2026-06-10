from src.repositories.client_repository import ClientRepository


class AddToCartUseCase:
    def __init__(self, client_repository: ClientRepository):
        self.client_repository = client_repository
        # TODO: injetar CarrinhoRepository quando disponível

    def execute(self, client_id: int, produto_id: int, quantidade: int) -> None:
        client = self.client_repository.get_by_id(client_id)
        if not client:
            raise ValueError("Cliente não encontrado")

        client.adicionar_ao_carrinho(produto_id, quantidade)

        # TODO: integrar com CarrinhoRepository para persistir item no carrinho
        # Exemplo futuro:
        # self.cart_repository.add_item(client_id=client_id, produto_id=produto_id, quantidade=quantidade)
