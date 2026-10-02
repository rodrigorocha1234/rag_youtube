"""Contratos estritos da configuração operacional."""

import re
from string import Formatter
from typing import Literal, Self
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ConfiguracaoBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProjetoConfig(ConfiguracaoBase):
    nome: str
    arquivo_ambiente: str


class YoutubeConfig(ConfiguracaoBase):
    arquivo_ambiente: str
    segredo_ambiente: Literal["YOUTUBE_API_KEY"]
    ids_canais: list[str] = Field(min_length=1)
    dias_publicacao_atras: int = Field(ge=0)
    modo_janela_publicacao: Literal["dia_exato", "acumulada"]
    timezone: str
    incluir_respostas: bool
    max_resultados_pagina: int = Field(ge=1, le=100)
    limites_paginas: dict[str, int]
    url_api: str
    timeout_segundos: float = Field(gt=0)
    tentativas_requisicao: int = Field(ge=1)
    espera_retry_segundos: float = Field(ge=0)
    quota_maxima: int = Field(ge=1)
    custo_requisicao: int = Field(ge=1)
    status_retry: list[int]

    @field_validator("timezone")
    @classmethod
    def validar_timezone(cls, valor: str) -> str:
        try:
            ZoneInfo(valor)
        except ZoneInfoNotFoundError:
            raise ValueError("Timezone inválido") from None
        return valor

    @field_validator("ids_canais")
    @classmethod
    def validar_canais(cls, valores: list[str]) -> list[str]:
        if any(not valor.strip() for valor in valores):
            raise ValueError("Canal vazio")
        return valores

    @field_validator("limites_paginas")
    @classmethod
    def validar_limites(cls, valores: dict[str, int]) -> dict[str, int]:
        recursos = {"channels", "playlistItems", "commentThreads", "comments"}
        if valores.keys() != recursos or any(valor <= 0 for valor in valores.values()):
            raise ValueError("Limites de paginação inválidos")
        return valores


class DatalakeConfig(ConfiguracaoBase):
    diretorio_raiz: str
    camada_bronze: str
    camada_prata: str
    camada_ouro: str


class RagConfig(ConfiguracaoBase):
    estrategia_recuperacao: Literal["semantica", "hibrida"]
    recuperar_documentos: int = Field(gt=0)
    reranking_habilitado: bool
    peso_semantico: float = Field(ge=0, le=1)
    peso_lexical: float = Field(ge=0, le=1)
    constante_rrf: int = Field(gt=0)

    @model_validator(mode="after")
    def validar_pesos(self) -> Self:
        if self.peso_semantico + self.peso_lexical <= 0:
            raise ValueError("Pesos da recuperação precisam ser positivos")
        return self


class MlflowConfig(ConfiguracaoBase):
    habilitado: bool
    uri_rastreamento: str | None
    experimento: str


class ObservabilidadeConfig(ConfiguracaoBase):
    habilitada: bool
    namespace_metricas: str
    arquivo_metricas: str
    nivel_log: str
    buckets_latencia: tuple[float, ...]

    @field_validator("buckets_latencia")
    @classmethod
    def validar_buckets(cls, valores: tuple[float, ...]) -> tuple[float, ...]:
        if (
            not valores
            or any(valor <= 0 for valor in valores)
            or tuple(sorted(set(valores))) != valores
        ):
            raise ValueError("Buckets devem ser positivos, distintos e crescentes")
        return valores


class VetorConfig(ConfiguracaoBase):
    usuario_ambiente: str
    senha_ambiente: str
    banco_ambiente: str
    porta_ambiente: str
    host: str
    driver: str
    conexao_ambiente: str
    inicializar_tabela: bool
    tabela: str
    esquema: str

    @field_validator("tabela", "esquema")
    @classmethod
    def validar_identificadores(cls, valor: str) -> str:
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", valor) is None:
            raise ValueError("Identificador SQL inválido")
        return valor


class ProjetoRagConfig(ConfiguracaoBase):
    projeto: ProjetoConfig
    youtube: YoutubeConfig
    datalake: DatalakeConfig
    rag: RagConfig
    mlflow: MlflowConfig
    observabilidade: ObservabilidadeConfig
    vetor: VetorConfig


class EmbeddingsConfig(ConfiguracaoBase):
    provedor: Literal["huggingface"]
    modelo: str
    normalizar: bool
    dispositivo: str
    tamanho_lote: int = Field(gt=0)
    dimensoes: int = Field(gt=0)


class GeracaoConfig(ConfiguracaoBase):
    provedor: Literal["huggingface"]
    modelo: str
    temperatura: float = Field(ge=0)
    max_tokens: int = Field(gt=0)
    tarefa: str
    dispositivo: int
    prompt_sem_contexto: str
    prompt_contexto: str

    @field_validator("prompt_contexto")
    @classmethod
    def validar_prompt(cls, valor: str) -> str:
        campos = {nome for _, nome, _, _ in Formatter().parse(valor) if nome is not None}
        if campos != {"pergunta", "contexto"}:
            raise ValueError("Prompt deve conter somente placeholders pergunta e contexto")
        return valor


class RerankingConfig(ConfiguracaoBase):
    habilitado: bool
    provedor: Literal["huggingface"]
    modelo: str
    quantidade_candidatos: int = Field(gt=0)
    quantidade_final: int = Field(gt=0)
    dispositivo: str


class ModelosRagConfig(ConfiguracaoBase):
    embeddings: EmbeddingsConfig
    geracao: GeracaoConfig
    reranking: RerankingConfig
