"""Fronteira tipada para o SDK MLflow."""

from contextlib import AbstractContextManager
from typing import Protocol

from integracao_mlflow.contrato_span import SpanMlflow


class SdkMlflow(Protocol):
    def set_tracking_uri(self, uri: str) -> None: ...
    def set_experiment(self, experiment_name: str) -> object: ...
    def start_span(self, name: str) -> AbstractContextManager[SpanMlflow]: ...
