"""Contrato opcional de reranking."""
from typing import Protocol

from documentos_rag.documento_rag import DocumentoRag


class ModeloReranking(Protocol):
    def ordenar_documentos(self, pergunta: str, documentos: list[DocumentoRag]) -> list[DocumentoRag]: ...
