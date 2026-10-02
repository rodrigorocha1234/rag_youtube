"""Estruturas de configuração do dashboard e exemplos de avaliação."""

from pydantic import BaseModel, ConfigDict, JsonValue


class ConfiguracaoDashboard(BaseModel):
    model_config = ConfigDict(extra="forbid")
    arquivo_projeto: str
    arquivo_serving: str
    arquivo_dataset: str
    arquivo_saida: str
    fonte_uid: str
    modelo: dict[str, JsonValue]


class EntradaAvaliacao(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str
    context: str


class SaidaAvaliacao(BaseModel):
    model_config = ConfigDict(extra="forbid")
    response: str


class ExpectativaAvaliacao(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_response: str
    expected_facts: list[str]
    documentos_relevantes: list[str]


class ExemploAvaliacao(BaseModel):
    model_config = ConfigDict(extra="forbid")
    inputs: EntradaAvaliacao
    outputs: SaidaAvaliacao
    expectations: ExpectativaAvaliacao
