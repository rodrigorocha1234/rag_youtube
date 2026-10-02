"""Registro Prata com proveniência."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ComentarioYoutube(BaseModel):
    model_config = ConfigDict(extra="forbid")
    canal_id: str
    video_id: str
    comentario_id: str
    comentario_pai_id: str | None
    texto_original: str
    texto_normalizado: str
    data_publicacao: datetime
    data_atualizacao: datetime
    quantidade_likes: int
    tipo_documento: Literal["comentario", "resposta"]
    data_ingestao: datetime
