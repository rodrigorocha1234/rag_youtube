"""Documento Ouro pronto para embeddings."""

from pydantic import BaseModel, ConfigDict


class DocumentoRag(BaseModel):
    model_config = ConfigDict(extra="forbid")
    documento_id: str
    conteudo: str
    metadados: dict[str, str | int | float | bool | None]
