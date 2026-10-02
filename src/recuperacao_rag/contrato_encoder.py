"""Fronteira tipada para dependência opcional CrossEncoder."""
from typing import Protocol


class PontuadorPares(Protocol):
    def predict(self, sentences: list[tuple[str, str]], *, convert_to_numpy: bool) -> object: ...
