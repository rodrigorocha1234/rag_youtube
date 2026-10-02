"""Observabilidade de etapas sem dependência de serviços externos."""

import json
import logging
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from time import perf_counter

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest

from integracao_mlflow.tracador_mlflow import TracadorMlflow
from observabilidade_app.seguranca_eventos import ValorEvento, limpar_eventos


class MonitorOperacao:
    """Publica contagens, latência, erros e medidas de qualidade."""

    def __init__(
        self,
        namespace: str,
        buckets: tuple[float, ...],
        segredos: tuple[str, ...] = (),
        habilitado: bool = True,
        tracador: TracadorMlflow | None = None,
    ) -> None:
        self.tracador = tracador
        self.habilitado = habilitado
        self.segredos = segredos
        self.registro = CollectorRegistry()
        self.logger = logging.getLogger(namespace)
        self.contagens = Counter(
            "eventos",
            "Quantidade de eventos por etapa",
            ("etapa",),
            namespace=namespace,
            registry=self.registro,
        )
        self.erros = Counter(
            "erros",
            "Falhas por etapa",
            ("etapa", "tipo"),
            namespace=namespace,
            registry=self.registro,
        )
        self.latencia = Histogram(
            "latencia_segundos",
            "Duração por etapa",
            ("etapa",),
            buckets=buckets,
            namespace=namespace,
            registry=self.registro,
        )
        self.qualidade = Gauge(
            "qualidade",
            "Medição de qualidade por critério",
            ("criterio",),
            namespace=namespace,
            registry=self.registro,
        )

    @contextmanager
    def envolver_etapa(
        self, nome: str, atributos: Mapping[str, ValorEvento] | None = None
    ) -> Iterator[None]:
        inicio = perf_counter()
        estado = "sucesso"
        try:
            if self.tracador is None:
                yield
            else:
                with self.tracador.envolver_etapa(nome, atributos):
                    yield
        except Exception as erro:
            estado = "erro"
            if self.habilitado:
                self.erros.labels(nome, type(erro).__name__).inc()
            raise
        finally:
            if self.habilitado:
                duracao = perf_counter() - inicio
                self.latencia.labels(nome).observe(duracao)
                eventos = limpar_eventos(atributos or {}, self.segredos)
                eventos.update(etapa=nome, estado=estado, duracao_segundos=duracao)
                self.logger.info(json.dumps(eventos, ensure_ascii=False))

    def registrar_contagem(self, nome: str, quantidade: float = 1) -> None:
        if self.habilitado:
            self.contagens.labels(nome).inc(quantidade)

    def registrar_qualidade(self, nome: str, valor: float) -> None:
        if self.habilitado:
            self.qualidade.labels(nome).set(valor)

    def exportar_metricas(self) -> bytes:
        return generate_latest(self.registro)
