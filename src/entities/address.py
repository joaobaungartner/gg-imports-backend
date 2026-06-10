import re
from dataclasses import dataclass

CEP_REGEX = re.compile(r"^\d{8}$")
ESTADO_REGEX = re.compile(r"^[A-Z]{2}$")


@dataclass
class AddressEntity:
    id: int | None
    client_id: int
    rua: str
    numero: str
    bairro: str
    cidade: str
    estado: str
    cep: str
    ativo: bool = True

    def __post_init__(self) -> None:
        self.estado = self.estado.strip().upper()
        self._normalize_cep()
        self.validar_endereco()

    def _normalize_cep(self) -> None:
        self.cep = re.sub(r"\D", "", self.cep)

    def validar_cep(self) -> bool:
        self._normalize_cep()
        return bool(CEP_REGEX.match(self.cep))

    def validar_endereco(self) -> None:
        if not self.rua or not self.rua.strip():
            raise ValueError("Rua é obrigatória")
        if not self.numero or not self.numero.strip():
            raise ValueError("Número é obrigatório")
        if not self.bairro or not self.bairro.strip():
            raise ValueError("Bairro é obrigatório")
        if not self.cidade or not self.cidade.strip():
            raise ValueError("Cidade é obrigatória")
        if not self.estado or not ESTADO_REGEX.match(self.estado):
            raise ValueError("Estado inválido")
        if not self.validar_cep():
            raise ValueError("CEP inválido")
        if not self.client_id:
            raise ValueError("Cliente não encontrado")

    def atualizar_endereco(
        self,
        rua: str | None = None,
        numero: str | None = None,
        bairro: str | None = None,
        cidade: str | None = None,
        estado: str | None = None,
        cep: str | None = None,
    ) -> None:
        if rua is not None:
            self.rua = rua.strip()
        if numero is not None:
            self.numero = numero.strip()
        if bairro is not None:
            self.bairro = bairro.strip()
        if cidade is not None:
            self.cidade = cidade.strip()
        if estado is not None:
            self.estado = estado.strip().upper()
        if cep is not None:
            self.cep = cep
            self._normalize_cep()
        self.validar_endereco()

    def endereco_completo(self) -> str:
        cep_formatado = f"{self.cep[:5]}-{self.cep[5:]}" if len(self.cep) == 8 else self.cep
        return (
            f"{self.rua}, {self.numero} - {self.bairro}, "
            f"{self.cidade}/{self.estado} - CEP {cep_formatado}"
        )

    def desativar(self) -> None:
        self.ativo = False
