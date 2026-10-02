"""Registro explícito das estratégias disponíveis."""
from recuperacao_rag.contratos_busca import FonteBusca


class RegistroEstrategias:
    def __init__(self, estrategias: dict[str, FonteBusca]) -> None:
        self.estrategias = estrategias

    def obter_estrategia(self, nome: str) -> FonteBusca:
        try:
            return self.estrategias[nome]
        except KeyError as erro:
            raise ValueError(f"Estratégia de recuperação desconhecida: {nome}") from erro
