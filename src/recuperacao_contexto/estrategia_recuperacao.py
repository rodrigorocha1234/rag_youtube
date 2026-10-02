from abc import ABC, abstractmethod
from collections.abc import Sequence


class EstrategiaRecuperacao(ABC):
    @abstractmethod
    def recuperar_documentos(self, pergunta: str) -> Sequence[str]: ...
