"""Orquestra as camadas do lake e os adapters RAG configurados."""

import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL

from armazenamento_lake.repositorio_lake import RepositorioLake
from coleta_youtube.cliente_youtube import ClienteYoutube
from coleta_youtube.coletor_comentarios import ColetorComentarios
from configuracao_app.carregador_config import CarregadorConfig
from configuracao_app.modelos_config import ModelosRagConfig, ProjetoRagConfig
from documentos_rag.construtor_documentos import ConstrutorDocumentos
from dominio_youtube.tipos_json import ObjetoJson
from geracao_resposta.resposta_fontes import RespostaFontes
from integracao_mlflow.tracador_mlflow import TracadorMlflow
from observabilidade_app.monitor_operacao import MonitorOperacao
from recuperacao_rag.contratos_busca import FiltrosBusca
from recuperacao_rag.fabrica_servico import construir_servico
from tratamento_texto.normalizador_texto import NormalizadorTexto


class ExecucaoPipeline:
    def __init__(self, projeto: ProjetoRagConfig, modelos: ModelosRagConfig, raiz: Path) -> None:
        self.projeto = projeto
        self.modelos = modelos
        self.raiz = raiz

    def preparar_ambiente(self) -> None:
        load_dotenv(self.raiz / self.projeto.projeto.arquivo_ambiente, override=False)
        config = self.projeto.vetor
        if not os.environ.get(config.conexao_ambiente):
            valores = [
                os.environ.get(nome)
                for nome in (
                    config.usuario_ambiente,
                    config.senha_ambiente,
                    config.banco_ambiente,
                    config.porta_ambiente,
                )
            ]
            if any(valor is None for valor in valores):
                raise ValueError("Variáveis de conexão PostgreSQL ausentes")
            usuario, senha, banco, porta = valores
            assert porta is not None
            conexao = URL.create(
                config.driver,
                username=usuario,
                password=senha,
                host=config.host,
                port=int(porta),
                database=banco,
            )
            os.environ[config.conexao_ambiente] = conexao.render_as_string(hide_password=False)

    def executar_fluxo(self, pergunta: str | None, filtros: FiltrosBusca) -> RespostaFontes | None:
        CarregadorConfig.validar_operacao(self.projeto, self.modelos)
        segredo = CarregadorConfig.carregar_segredo(self.projeto, self.raiz)
        self.preparar_ambiente()
        config_mlflow = self.projeto.mlflow
        uri = (
            os.path.expandvars(config_mlflow.uri_rastreamento)
            if config_mlflow.uri_rastreamento
            else None
        )
        segredos = tuple(
            valor
            for valor in (
                segredo.get_secret_value(),
                os.environ.get(self.projeto.vetor.senha_ambiente),
                os.environ.get(self.projeto.vetor.conexao_ambiente),
            )
            if valor
        )
        tracador = TracadorMlflow(
            config_mlflow.habilitado, uri, config_mlflow.experimento, segredos
        )
        obs = self.projeto.observabilidade
        logging.basicConfig(level=obs.nivel_log, format="%(message)s")
        monitor = MonitorOperacao(
            obs.namespace_metricas, obs.buckets_latencia, segredos, obs.habilitada
        )
        lake = RepositorioLake(self.projeto.datalake, self.raiz)
        cliente = ClienteYoutube(self.projeto.youtube, segredo)
        instante = datetime.now(timezone.utc)

        def salvar_bronze(recurso: str, payload: ObjetoJson, quando: datetime) -> Path:
            destino = lake.salvar_bronze(recurso, payload, quando)
            monitor.registrar_contagem("bronze_paginas")
            return destino

        try:
            with monitor.envolver_etapa("youtube"), tracador.envolver_etapa("youtube") as saidas:
                coletor = ColetorComentarios(self.projeto.youtube, cliente, salvar_bronze)
                registros = coletor.coletar_canais(instante)
                saidas["registros"] = len(registros)
                monitor.registrar_contagem("youtube_quota", cliente.quota_consumida)
                monitor.registrar_contagem("comentarios_coletados", len(registros))
            with monitor.envolver_etapa("prata"), tracador.envolver_etapa("prata"):
                prata = NormalizadorTexto().normalizar_registros(registros)
                lake.salvar_prata(prata)
                monitor.registrar_contagem("prata", len(prata))
            with monitor.envolver_etapa("ouro"), tracador.envolver_etapa("ouro"):
                documentos = ConstrutorDocumentos().construir_documentos(prata)
                lake.salvar_ouro(documentos)
                monitor.registrar_contagem("ouro", len(documentos))
            if not documentos:
                return (
                    RespostaFontes(self.modelos.geracao.prompt_sem_contexto, (), False)
                    if pergunta
                    else None
                )
            componentes = construir_servico(
                self.projeto, self.modelos, documentos, monitor, tracador
            )
            return componentes.servico.responder_pergunta(pergunta, filtros) if pergunta else None
        finally:
            monitor.registrar_contagem(
                "youtube_requisicoes",
                cliente.quota_consumida / self.projeto.youtube.custo_requisicao,
            )
            destino = self.raiz / obs.arquivo_metricas
            destino.parent.mkdir(parents=True, exist_ok=True)
            temporario = destino.with_suffix(".tmp")
            temporario.write_bytes(monitor.exportar_metricas())
            temporario.replace(destino)
