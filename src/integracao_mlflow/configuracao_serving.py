"""Contratos da publicação e requisições de serving."""

from pydantic import BaseModel, ConfigDict, Field


class ConfiguracaoServing(BaseModel):
    model_config = ConfigDict(extra="forbid")
    arquivo_projeto: str
    arquivo_modelos: str
    nome_modelo: str
    nome_run: str
    arquivo_recibo: str
    arquivo_uri: str
    artefato_projeto: str
    artefato_modelos: str
    artefato_documentos: str
    arquivo_snapshot: str
    conexao_ambiente: str
    tracking_ambiente: str
    experimento_serving: str
    nome_modelo_ambiente: str
    host_ambiente: str
    indice_torch: str
    pacote_torch: str
    arquivo_requisitos: str
    arquivo_metricas: str
    namespace_metricas: str
    host_serving: str
    porta_serving: int = Field(gt=0, le=65535)
    workers_serving: int = Field(gt=0)
    timeout_serving: int = Field(gt=0)
    requisitos: list[str]


class PerguntaServing(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pergunta: str = Field(min_length=1)
    canal_id: str | None = None
    video_id: str | None = None
