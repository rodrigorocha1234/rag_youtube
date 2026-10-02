"""Modelo pyfunc para consultar o RAG sem ingestão por requisição."""

import logging
import os
from pathlib import Path
from typing import override
from uuid import uuid4

from mlflow.pyfunc.model import PythonModel, PythonModelContext
from sqlalchemy.engine import URL

from configuracao_app.carregador_config import CarregadorConfig
from documentos_rag.documento_rag import DocumentoRag
from dominio_youtube.tipos_json import ValorJson, validar_json
from geracao_resposta.servico_resposta import ServicoResposta
from integracao_mlflow.configuracao_serving import ConfiguracaoServing, PerguntaServing
from integracao_mlflow.tracador_mlflow import TracadorMlflow
from observabilidade_app.monitor_operacao import MonitorOperacao
from observabilidade_app.seguranca_eventos import limpar_valor
from recuperacao_rag.contratos_busca import FiltrosBusca
from recuperacao_rag.fabrica_servico import construir_servico


class ModeloConsulta(PythonModel):
    def __init__(self, config: ConfiguracaoServing) -> None:
        self.config = config
        self.servico: ServicoResposta | None = None

    @override
    def load_context(self, context: PythonModelContext) -> None:
        self.projeto = CarregadorConfig.carregar_projeto(
            Path(context.artifacts[self.config.artefato_projeto])
        )
        self.modelos = CarregadorConfig.carregar_modelos(
            Path(context.artifacts[self.config.artefato_modelos])
        )
        CarregadorConfig.validar_operacao(self.projeto, self.modelos)
        self.documentos = [
            DocumentoRag.model_validate_json(linha)
            for linha in Path(context.artifacts[self.config.artefato_documentos])
            .read_text()
            .splitlines()
            if linha.strip()
        ]
        self.segredos = tuple(
            valor
            for valor in (
                os.environ.get(self.projeto.vetor.conexao_ambiente),
                os.environ.get(self.projeto.vetor.senha_ambiente),
            )
            if valor
        )
        uri = os.environ.get(self.config.tracking_ambiente)
        self.tracador = TracadorMlflow(
            self.projeto.mlflow.habilitado, uri, self.config.experimento_serving, self.segredos
        )
        obs = self.projeto.observabilidade
        logging.basicConfig(level=obs.nivel_log, format="%(message)s")
        logging.getLogger(self.config.namespace_metricas).setLevel(obs.nivel_log)
        self.monitor = MonitorOperacao(
            self.config.namespace_metricas, obs.buckets_latencia, self.segredos, obs.habilitada
        )
        if self.documentos:
            config_vetor = self.projeto.vetor
            if not os.environ.get(config_vetor.conexao_ambiente):
                porta = os.environ[config_vetor.porta_ambiente]
                url = URL.create(
                    config_vetor.driver,
                    username=os.environ[config_vetor.usuario_ambiente],
                    password=os.environ[config_vetor.senha_ambiente],
                    host=os.environ[self.config.host_ambiente],
                    port=int(porta),
                    database=os.environ[config_vetor.banco_ambiente],
                )
                os.environ[config_vetor.conexao_ambiente] = url.render_as_string(
                    hide_password=False
                )
            componentes = construir_servico(
                self.projeto,
                self.modelos,
                self.documentos,
                self.monitor,
                self.tracador,
                indexar=False,
            )
            self.servico = componentes.servico

    @override
    def predict(
        self,
        context: PythonModelContext,
        model_input: list[dict[str, str]],
        params: dict[str, object] | None = None,
    ) -> list[dict[str, object]]:
        perguntas = [PerguntaServing.model_validate(entrada) for entrada in model_input]
        resultados: list[dict[str, object]] = []
        try:
            for entrada in perguntas:
                with (
                    self.monitor.envolver_etapa("servir_resposta"),
                    self.tracador.envolver_etapa(
                        "servir_resposta", {"pergunta": entrada.pergunta}
                    ) as saidas,
                ):
                    filtros: FiltrosBusca = {}
                    if entrada.canal_id:
                        filtros["canal_id"] = entrada.canal_id
                    if entrada.video_id:
                        filtros["video_id"] = entrada.video_id
                    resultado: dict[str, ValorJson]
                    if self.servico is None:
                        resultado = {
                            "resposta": self.modelos.geracao.prompt_sem_contexto,
                            "fontes": [],
                        }
                    else:
                        resposta = self.servico.responder_pergunta(entrada.pergunta, filtros)
                        resultado = {
                            "resposta": resposta.texto,
                            "fontes": [validar_json(doc.model_dump()) for doc in resposta.fontes],
                        }
                    seguro = limpar_valor(resultado, self.segredos)
                    assert isinstance(seguro, dict)
                    resultados.append(seguro)
                    saidas["resposta"] = str(seguro["resposta"])
                    self.monitor.registrar_contagem("respostas_servidas")
            return resultados
        finally:
            destino = Path(self.config.arquivo_metricas)
            destino.parent.mkdir(parents=True, exist_ok=True)
            temporario = destino.with_name(f"{destino.name}.{uuid4().hex}.tmp")
            temporario.write_bytes(self.monitor.exportar_metricas())
            temporario.replace(destino)
