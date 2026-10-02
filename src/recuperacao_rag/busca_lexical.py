"""Busca lexical local vetorizável sobre um corpus Ouro limitado."""
import re

from documentos_rag.documento_rag import DocumentoRag
from recuperacao_rag.contratos_busca import FiltrosBusca
from recuperacao_rag.filtros_metadados import verificar_filtros


class BuscaLexical:
    def __init__(self, documentos: list[DocumentoRag]) -> None:
        self.documentos = documentos

    def buscar_documentos(self, pergunta: str, quantidade: int, filtros: FiltrosBusca) -> list[DocumentoRag]:
        termos = set(re.findall(r"\w+", pergunta.casefold()))
        candidatos = [documento for documento in self.documentos
                      if verificar_filtros(documento.metadados, filtros)]
        pontuados = [(len(termos.intersection(re.findall(r"\w+", documento.conteudo.casefold()))), documento)
                     for documento in candidatos]
        return [documento for pontos, documento in sorted(pontuados, key=lambda item: (-item[0], item[1].documento_id))
                if pontos > 0][:quantidade]
