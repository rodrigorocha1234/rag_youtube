"""Estratégia de busca por proximidade vetorial."""
from documentos_rag.documento_rag import DocumentoRag
from recuperacao_rag.contratos_busca import FiltrosBusca, FonteBusca


class EstrategiaSemantica:
    def __init__(self, fonte: FonteBusca) -> None:
        self.fonte = fonte

    def buscar_documentos(self, pergunta: str, quantidade: int, filtros: FiltrosBusca) -> list[DocumentoRag]:
        return self.fonte.buscar_documentos(pergunta, quantidade, filtros)
