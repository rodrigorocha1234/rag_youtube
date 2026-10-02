"""Tracing GenAI com sanitização antes de cruzar a fronteira do SDK."""

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from importlib import import_module
from typing import cast

from integracao_mlflow.contrato_sdk import SdkMlflow
from observabilidade_app.seguranca_eventos import ValorEvento, limpar_eventos


class TracadorMlflow:
    def __init__(
        self,
        habilitado: bool,
        uri: str | None,
        experimento: str,
        segredos: tuple[str, ...] = (),
        sdk: SdkMlflow | None = None,
    ) -> None:
        self.segredos = segredos
        self.sdk = (sdk or cast(SdkMlflow, import_module("mlflow"))) if habilitado else None
        if self.sdk is not None:
            if uri is None:
                raise ValueError("MLflow habilitado requer URI de rastreamento")
            self.sdk.set_tracking_uri(uri)
            self.sdk.set_experiment(experimento)

    @contextmanager
    def envolver_etapa(
        self, nome: str, entradas: Mapping[str, ValorEvento] | None = None
    ) -> Iterator[dict[str, ValorEvento]]:
        saidas: dict[str, ValorEvento] = {}
        if self.sdk is None:
            yield saidas
            return
        falha: Exception | None = None
        with self.sdk.start_span(name=nome) as span:
            span.set_inputs(limpar_eventos(entradas or {}, self.segredos))
            try:
                yield saidas
            except Exception as erro:
                # Nunca entregue mensagens de exceção do provedor ao SDK.
                falha = erro
                span.set_status("ERROR")
                span.set_attributes({"estado": "erro", "tipo_erro": type(erro).__name__})
            finally:
                span.set_outputs(limpar_eventos(saidas, self.segredos))
        if falha is not None:
            raise falha
