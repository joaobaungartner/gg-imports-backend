from dataclasses import dataclass


@dataclass
class CategoryEntity:
    id: int | None
    nome: str
    descricao: str | None = None
    ativo: bool = True

    def __post_init__(self) -> None:
        self.nome = self.nome.strip()
        if self.descricao is not None:
            self.descricao = self.descricao.strip() or None
        self.validar_categoria()

    def validar_categoria(self) -> None:
        if not self.nome:
            raise ValueError("Nome da categoria é obrigatório")

    def atualizar_categoria(
        self,
        nome: str | None = None,
        descricao: str | None = None,
        ativo: bool | None = None,
    ) -> None:
        if nome is not None:
            self.nome = nome.strip()
        if descricao is not None:
            self.descricao = descricao.strip() or None
        if ativo is not None:
            self.ativo = ativo
        self.validar_categoria()

    def ativar(self) -> None:
        self.ativo = True

    def desativar(self) -> None:
        self.ativo = False

    def esta_ativa(self) -> bool:
        return self.ativo
