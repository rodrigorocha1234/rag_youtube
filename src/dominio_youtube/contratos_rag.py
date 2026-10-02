from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True, slots=True)
class DocumentoRag:
    id_documento: str
    texto: str
    id_canal: str
    id_video: str
    hash_conteudo: str
    metadata: dict[str, str] = field(default_factory=dict)
    score: float | None = None


@dataclass(frozen=True, slots=True)
class RespostaRag:
    resposta: str
    documentos: tuple[DocumentoRag, ...]
    contexto: str


class RepositorioDocumentos(Protocol):
    def indexar_documentos(self, documentos: Sequence[DocumentoRag]) -> int: ...
    def buscar_documentos(
        self, pergunta: str, filtros: dict[str, str], quantidade: int
    ) -> list[DocumentoRag]: ...


class ReordenadorDocumentos(Protocol):
    def reordenar_documentos(
        self, pergunta: str, documentos: Sequence[DocumentoRag]
    ) -> list[DocumentoRag]: ...


class GeradorRespostas(Protocol):
    def gerar_resposta(self, pergunta: str, contexto: str) -> str: ...
