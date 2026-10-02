"""Contrato real de PGVectorStore com embeddings determinísticos, opt-in."""

import os
import re
from pathlib import Path
from typing import override

import pytest
from langchain_core.embeddings import Embeddings
from sqlalchemy import create_engine, inspect, text

from armazenamento_vetor.repositorio_pgvector import RepositorioPgvector
from configuracao_app.carregador_config import CarregadorConfig
from documentos_rag.documento_rag import DocumentoRag
from pipeline_principal.execucao_pipeline import ExecucaoPipeline


class EmbeddingsTeste(Embeddings):
    def __init__(self, dimensoes: int) -> None:
        self.dimensoes = dimensoes

    @override
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(texto) for texto in texts]

    @override
    def embed_query(self, text: str) -> list[float]:
        return [1.0] + [0.0] * (self.dimensoes - 1)


@pytest.mark.externo
def test_pgvector_real_idempotencia_filtros() -> None:
    nomes = ("RAG_TESTE_PROJETO", "RAG_TESTE_MODELOS", "RAG_TESTE_RAIZ", "RAG_TESTE_TABELA")
    if not all(os.environ.get(nome) for nome in nomes):
        pytest.skip("Integração PostgreSQL requer configuração explícita por ambiente")
    projeto = CarregadorConfig.carregar_projeto(Path(os.environ[nomes[0]]))
    modelos = CarregadorConfig.carregar_modelos(Path(os.environ[nomes[1]]))
    ExecucaoPipeline(projeto, modelos, Path(os.environ[nomes[2]])).preparar_ambiente()
    tabela = os.environ[nomes[3]]
    assert re.fullmatch(r"[a-z][a-z0-9_]*", tabela)
    assert tabela != projeto.vetor.tabela
    conexao = os.environ[projeto.vetor.conexao_ambiente]
    embeddings = EmbeddingsTeste(modelos.embeddings.dimensoes)
    motor = create_engine(conexao)
    assert not inspect(motor).has_table(tabela, schema=projeto.vetor.esquema), (
        "Tabela de teste já existe; preservada"
    )
    try:
        banco = RepositorioPgvector.criar_repositorio(
            conexao, tabela, projeto.vetor.esquema, embeddings, modelos.embeddings.dimensoes, True
        )
        documento = DocumentoRag(
            documento_id="contrato",
            conteudo="Comentário para validar integração",
            metadados={"canal_id": "canal_teste", "data_publicacao": "2026-10-01T12:00:00+00:00"},
        )
        banco.salvar_documentos([documento])
        banco.salvar_documentos([documento])
        # Outra inicialização precisa preservar dados.
        banco = RepositorioPgvector.criar_repositorio(
            conexao, tabela, projeto.vetor.esquema, embeddings, modelos.embeddings.dimensoes, True
        )
        documentos = banco.buscar_documentos(
            "integração", projeto.rag.recuperar_documentos, {"canal_id": "canal_teste"}
        )
        assert len(documentos) == 1 and documentos[0].documento_id == "contrato"
        assert not banco.buscar_documentos(
            "integração", projeto.rag.recuperar_documentos, {"canal_id": "outro"}
        )
    finally:
        esquema = projeto.vetor.esquema
        with motor.begin() as sessao:
            sessao.execute(text(f'DROP TABLE IF EXISTS "{esquema}"."{tabela}"'))
        motor.dispose()
