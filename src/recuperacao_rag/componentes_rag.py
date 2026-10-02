"""Componentes construídos para execução operacional."""
from dataclasses import dataclass

from langchain_core.embeddings import Embeddings

from armazenamento_vetor.repositorio_pgvector import RepositorioPgvector
from geracao_resposta.servico_resposta import ServicoResposta


@dataclass(frozen=True)
class ComponentesRag:
    banco: RepositorioPgvector
    embeddings: Embeddings
    servico: ServicoResposta
