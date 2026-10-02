"""Fronteira tipada para o SDK MLflow."""

from collections.abc import Mapping, Sequence
from typing import Protocol


class GenaiMlflow(Protocol):
    def evaluate(
        self, *, data: Sequence[Mapping[str, object]], scorers: Sequence[object]
    ) -> object: ...
