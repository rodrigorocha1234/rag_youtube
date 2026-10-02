"""Contrato do adaptador YouTube."""

from typing import Protocol

from dominio_youtube.tipos_json import ObjetoJson


class ConsultaYoutube(Protocol):
    def consultar_recurso(self, recurso: str, parametros: dict[str, str]) -> ObjetoJson: ...
