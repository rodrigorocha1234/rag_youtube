from collections.abc import Iterator
from contextlib import contextmanager

from integracao_mlflow.contrato_span import SpanMlflow
from testes_integracao.span_duplo import SpanDuplo


class SdkDuplo:
    def __init__(self) -> None:
        self.span = SpanDuplo()
        self.excecoes: list[str] = []

    def set_tracking_uri(self, uri: str) -> None:
        pass

    def set_experiment(self, experiment_name: str) -> object:
        return experiment_name

    @contextmanager
    def start_span(self, name: str) -> Iterator[SpanMlflow]:
        try:
            yield self.span
        except Exception as erro:
            self.excecoes.append(str(erro))
            raise
