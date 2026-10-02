from typing import cast

from langchain_core.documents import Document
from langchain_postgres import PGVectorStore

from armazenamento_vetor.repositorio_pgvector import RepositorioPgvector
from documentos_rag.documento_rag import DocumentoRag


class ArmazenamentoDuplo:
    def __init__(self) -> None:
        self.documentos: list[Document] = []
        self.filtros: dict[str, object] | None = None
        self.ids: list[str] = []

    def add_documents(self, documentos: list[Document], *, ids: list[str]) -> list[str]:
        self.documentos = documentos
        self.ids = ids
        return ids

    def similarity_search(self, pergunta: str, *, k: int,
                          filter: dict[str, object] | None) -> list[Document]:
        self.filtros = filter
        return self.documentos[:k]


def test_adapter_persiste_ids_estaveis_metadados_e_filtros() -> None:
    armazenamento = ArmazenamentoDuplo()
    repositorio = RepositorioPgvector(cast(PGVectorStore, armazenamento))
    documento = DocumentoRag(documento_id="comentario:1", conteudo="Texto", metadados={"canal_id": "canal"})
    ids = repositorio.salvar_documentos([documento])
    assert repositorio.salvar_documentos([documento]) == ids
    assert repositorio.buscar_documentos("Texto", 1, {"canal_id": "canal"})[0].documento_id == documento.documento_id
    assert armazenamento.filtros == {"canal_id": {"$eq": "canal"}}
    assert armazenamento.documentos[0].metadata["canal_id"] == "canal"


def test_intervalo_pgvector_usa_conjuncao_de_operadores() -> None:
    armazenamento = ArmazenamentoDuplo()
    repositorio = RepositorioPgvector(cast(PGVectorStore, armazenamento))
    repositorio.buscar_documentos("Texto", 1, {"data_publicacao": {"$gte": "2026-09-01", "$lte": "2026-09-30"}})
    assert armazenamento.filtros == {"$and": [
        {"data_publicacao": {"$gte": "2026-09-01"}},
        {"data_publicacao": {"$lte": "2026-09-30"}},
    ]}
