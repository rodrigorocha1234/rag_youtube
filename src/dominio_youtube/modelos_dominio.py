from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class EscopoRecuperacao(StrEnum):
    CANAL = "canal"
    VIDEO = "video"
    CANAL_VIDEO = "canal_video"


@dataclass(frozen=True, slots=True)
class ComentarioYoutube:
    id_comentario: str
    id_thread: str
    id_video: str
    id_canal: str
    texto: str
    data_publicacao: datetime
    data_atualizacao: datetime
    id_comentario_pai: str | None = None


@dataclass(frozen=True, slots=True)
class ConsultaRag:
    pergunta: str
    escopo: EscopoRecuperacao
    id_canal: str | None = None
    id_video: str | None = None
