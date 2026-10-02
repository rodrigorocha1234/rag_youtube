"""Execução explícita de avaliações MLflow GenAI por escopo."""

from collections.abc import Mapping, Sequence
from importlib import import_module
from typing import cast

from integracao_mlflow.contrato_genai import GenaiMlflow
from observabilidade_app.seguranca_eventos import limpar_valor


class AvaliadorGenai:
    def __init__(self, sdk: GenaiMlflow | None = None, segredos: tuple[str, ...] = ()) -> None:
        self.segredos = segredos
        self.sdk = sdk or cast(GenaiMlflow, import_module("mlflow.genai"))

    def avaliar_dataset(
        self, dados: Sequence[Mapping[str, object]], avaliadores: Mapping[str, Sequence[object]]
    ) -> dict[str, object]:
        if not dados:
            raise ValueError("Dataset de avaliação vazio")
        exigidos = {"retrieval", "geracao", "completo"}
        if set(avaliadores) != exigidos or any(not itens for itens in avaliadores.values()):
            raise ValueError("Configure scorers de retrieval, geracao e completo")
        seguros = cast(list[Mapping[str, object]], limpar_valor(list(dados), self.segredos))
        return {
            escopo: self.sdk.evaluate(data=seguros, scorers=scorers)
            for escopo, scorers in avaliadores.items()
        }
