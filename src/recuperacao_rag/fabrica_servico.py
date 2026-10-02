"""Composição dos adapters exclusivamente a partir de configuração validada."""

import os

from armazenamento_vetor.repositorio_pgvector import RepositorioPgvector
from configuracao_app.modelos_config import ModelosRagConfig, ProjetoRagConfig
from documentos_rag.documento_rag import DocumentoRag
from embeddings_texto.embeddings_huggingface import criar_embeddings
from geracao_resposta.gerador_huggingface import GeradorHuggingface
from geracao_resposta.servico_resposta import ServicoResposta
from integracao_mlflow.tracador_mlflow import TracadorMlflow
from observabilidade_app.monitor_operacao import MonitorOperacao
from recuperacao_rag.busca_lexical import BuscaLexical
from recuperacao_rag.componentes_rag import ComponentesRag
from recuperacao_rag.estrategia_hibrida import EstrategiaHibrida
from recuperacao_rag.estrategia_semantica import EstrategiaSemantica
from recuperacao_rag.registro_estrategias import RegistroEstrategias
from recuperacao_rag.reranking_huggingface import RerankingHuggingface


def construir_servico(
    projeto: ProjetoRagConfig,
    modelos: ModelosRagConfig,
    documentos: list[DocumentoRag],
    monitor: MonitorOperacao,
    tracador: TracadorMlflow,
    *,
    indexar: bool = True,
) -> ComponentesRag:
    conexao = os.environ.get(projeto.vetor.conexao_ambiente)
    if not conexao:
        raise ValueError("Conexão vetorial não configurada no ambiente")
    embedding = modelos.embeddings
    with (
        monitor.envolver_etapa("carregar_embeddings"),
        tracador.envolver_etapa("carregar_embeddings"),
    ):
        embeddings = criar_embeddings(
            embedding.modelo, embedding.dispositivo, embedding.normalizar, embedding.tamanho_lote
        )
    with (
        monitor.envolver_etapa("indexar_documentos" if indexar else "conectar_indice"),
        tracador.envolver_etapa("indexar_documentos" if indexar else "conectar_indice") as saidas,
    ):
        repositorio = RepositorioPgvector.criar_repositorio(
            conexao,
            projeto.vetor.tabela,
            projeto.vetor.esquema,
            embeddings,
            embedding.dimensoes,
            projeto.vetor.inicializar_tabela if indexar else False,
        )
        if indexar:
            repositorio.salvar_documentos(documentos)
            monitor.registrar_contagem("documentos_indexados", len(documentos))
        saidas["quantidade_documentos"] = len(documentos)
    semantica = EstrategiaSemantica(repositorio)
    hibrida = EstrategiaHibrida(
        semantica,
        BuscaLexical(documentos),
        projeto.rag.peso_semantico,
        projeto.rag.peso_lexical,
        projeto.rag.constante_rrf,
    )
    busca = RegistroEstrategias({"semantica": semantica, "hibrida": hibrida}).obter_estrategia(
        projeto.rag.estrategia_recuperacao
    )
    geracao = modelos.geracao
    gerador = GeradorHuggingface(
        geracao.modelo, geracao.tarefa, geracao.dispositivo, geracao.temperatura, geracao.max_tokens
    )
    reordenacao = modelos.reranking
    reranking = (
        RerankingHuggingface(reordenacao.modelo, reordenacao.dispositivo)
        if projeto.rag.reranking_habilitado and reordenacao.habilitado
        else None
    )
    quantidade_final = (
        min(projeto.rag.recuperar_documentos, reordenacao.quantidade_final)
        if reranking
        else projeto.rag.recuperar_documentos
    )
    quantidade_candidatos = reordenacao.quantidade_candidatos if reranking else quantidade_final
    if quantidade_candidatos < quantidade_final:
        raise ValueError("Quantidade de candidatos inferior ao top-k final")
    servico = ServicoResposta(
        busca,
        gerador,
        quantidade_candidatos,
        quantidade_final,
        geracao.prompt_contexto,
        geracao.prompt_sem_contexto,
        reranking,
        monitor,
        tracador,
    )

    return ComponentesRag(repositorio, embeddings, servico)
