from dominio_youtube.modelos_dominio import EscopoRecuperacao
from recuperacao_contexto.estrategia_recuperacao import EstrategiaRecuperacao


class FabricaRecuperacao:
    def __init__(self, estrategias: dict[EscopoRecuperacao, EstrategiaRecuperacao]) -> None:
        self._estrategias = estrategias

    def criar_estrategia(self, escopo: EscopoRecuperacao) -> EstrategiaRecuperacao:
        try:
            return self._estrategias[escopo]
        except KeyError as erro:
            raise ValueError(f"Escopo de recuperação não configurado: {escopo}") from erro
