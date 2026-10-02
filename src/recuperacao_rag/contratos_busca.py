"""Contratos de recuperação independentes dos provedores."""
from typing import Protocol

from documentos_rag.documento_rag import DocumentoRag

type ValorFiltro = str | int | float | bool | None
type CondicaoFiltro = ValorFiltro | dict[str, ValorFiltro]
type FiltrosBusca = dict[str, CondicaoFiltro]


class FonteBusca(Protocol):
    def buscar_documentos(self, pergunta: str, quantidade: int, filtros: FiltrosBusca) -> list[DocumentoRag]: ...
