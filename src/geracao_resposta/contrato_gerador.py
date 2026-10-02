"""Contrato para geração textual."""
from typing import Protocol


class GeradorTexto(Protocol):
    def gerar_texto(self, prompt: str) -> str: ...
