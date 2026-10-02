from collections.abc import Mapping

from observabilidade_app.seguranca_eventos import ValorEvento


class SpanDuplo:
    def __init__(self) -> None:
        self.estado = "UNSET"
        self.entradas: Mapping[str, ValorEvento] = {}
        self.saidas: Mapping[str, ValorEvento] = {}
        self.atributos: Mapping[str, ValorEvento] = {}

    def set_inputs(self, inputs: Mapping[str, ValorEvento]) -> None:
        self.entradas = inputs

    def set_outputs(self, outputs: Mapping[str, ValorEvento]) -> None:
        self.saidas = outputs

    def set_attributes(self, attributes: Mapping[str, ValorEvento]) -> None:
        self.atributos = attributes

    def set_status(self, status: str) -> None:
        self.estado = status
