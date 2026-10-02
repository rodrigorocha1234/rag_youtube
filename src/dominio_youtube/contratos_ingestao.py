from dataclasses import dataclass
from datetime import datetime

from pydantic import JsonValue, TypeAdapter

ADAPTADOR_JSON = TypeAdapter[JsonValue](JsonValue)


def objeto_json(valor: JsonValue) -> dict[str, JsonValue]:
    if not isinstance(valor, dict):
        raise ValueError("Objeto JSON esperado")
    return valor


def itens_json(pagina: dict[str, JsonValue]) -> list[dict[str, JsonValue]]:
    itens = pagina.get("items", [])
    if not isinstance(itens, list):
        raise ValueError("Lista de itens esperada")
    return [objeto_json(item) for item in itens]


def texto_json(valor: JsonValue) -> str:
    if not isinstance(valor, str):
        raise ValueError("Texto JSON esperado")
    return valor


@dataclass(frozen=True, slots=True)
class VideoYoutube:
    id_video: str
    id_canal: str
    titulo: str
    data_publicacao: datetime
    titulo_canal: str = ""


@dataclass(frozen=True, slots=True)
class ComentarioNormalizado:
    id_comentario: str
    id_thread: str
    id_video: str
    id_canal: str
    autor: str
    texto: str
    data_publicacao: datetime
    data_atualizacao: datetime
    curtidas: int
    hash_conteudo: str
    id_comentario_pai: str | None = None
    resposta: bool = False


@dataclass(frozen=True, slots=True)
class DocumentoSemantico:
    id_documento: str
    id_canal: str
    id_video: str
    id_thread: str
    texto: str
    hash_conteudo: str
    quantidade_comentarios: int
    curtidas: int
    titulo_video: str
    data_atualizacao: datetime
    titulo_canal: str = ""
