"""Adapter moderno PGVectorStore; inicialização de tabela explícita."""

from typing import TYPE_CHECKING, cast
from uuid import NAMESPACE_URL, uuid5

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import make_url

from documentos_rag.documento_rag import DocumentoRag
from recuperacao_rag.contratos_busca import FiltrosBusca, ValorFiltro
from recuperacao_rag.filtros_metadados import converter_filtros

if TYPE_CHECKING:
    from langchain_postgres import PGVectorStore


class RepositorioPgvector:
    def __init__(self, armazenamento: "PGVectorStore") -> None:
        self.armazenamento = armazenamento

    @classmethod
    def criar_repositorio(
        cls,
        conexao: str,
        tabela: str,
        esquema: str,
        embeddings: Embeddings,
        dimensoes: int,
        inicializar: bool,
    ) -> "RepositorioPgvector":
        from langchain_postgres import PGEngine, PGVectorStore

        motor: PGEngine = PGEngine.from_connection_string(url=conexao)
        if inicializar:
            verificacao = create_engine(make_url(conexao))
            try:
                existente = inspect(verificacao).has_table(tabela, schema=esquema)
            finally:
                verificacao.dispose()
            if not existente:
                motor.init_vectorstore_table(
                    table_name=tabela, schema_name=esquema, vector_size=dimensoes
                )
        armazenamento = PGVectorStore.create_sync(
            engine=motor, embedding_service=embeddings, table_name=tabela, schema_name=esquema
        )
        return cls(armazenamento)

    def salvar_documentos(self, documentos: list[DocumentoRag]) -> list[str]:
        itens = [
            Document(
                page_content=doc.conteudo,
                metadata={**doc.metadados, "documento_id": doc.documento_id},
            )
            for doc in documentos
        ]
        ids = [str(uuid5(NAMESPACE_URL, doc.documento_id)) for doc in documentos]
        return self.armazenamento.add_documents(itens, ids=ids)

    def buscar_documentos(
        self, pergunta: str, quantidade: int, filtros: FiltrosBusca
    ) -> list[DocumentoRag]:
        documentos = self.armazenamento.similarity_search(
            pergunta, k=quantidade, filter=converter_filtros(filtros) or None
        )
        resultado: list[DocumentoRag] = []
        for doc in documentos:
            metadados = cast(dict[str, ValorFiltro], doc.metadata)
            identificador = metadados.get("documento_id")
            if not isinstance(identificador, str):
                raise ValueError("Documento persistido sem proveniência")
            resultado.append(
                DocumentoRag(
                    documento_id=identificador, conteudo=doc.page_content, metadados=metadados
                )
            )
        return resultado
