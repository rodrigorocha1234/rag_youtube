"""Adapter HTTP com quota e retries, sem registrar URL autenticada."""

import json
import time
from collections.abc import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from pydantic import SecretStr

from configuracao_app.modelos_config import YoutubeConfig
from dominio_youtube.tipos_json import ObjetoJson, obter_objeto, validar_json


class ClienteYoutube:
    def __init__(
        self,
        config: YoutubeConfig,
        segredo: SecretStr,
        esperar: Callable[[float], None] = time.sleep,
    ) -> None:
        self.config = config
        self.segredo = segredo
        self.esperar = esperar
        self.quota_consumida = 0

    def consultar_recurso(self, recurso: str, parametros: dict[str, str]) -> ObjetoJson:
        consulta = urlencode({**parametros, "key": self.segredo.get_secret_value()})
        url = f"{self.config.url_api.rstrip('/')}/{recurso}?{consulta}"
        for tentativa in range(self.config.tentativas_requisicao):
            if self.quota_consumida + self.config.custo_requisicao > self.config.quota_maxima:
                raise RuntimeError("Quota YouTube esgotada")
            self.quota_consumida += self.config.custo_requisicao
            try:
                with urlopen(url, timeout=self.config.timeout_segundos) as resposta:
                    return obter_objeto(validar_json(json.loads(resposta.read())))
            except HTTPError as erro:
                try:
                    corpo = obter_objeto(validar_json(json.loads(erro.read())))
                except (ValueError, TypeError):
                    corpo = {}
                if "commentsDisabled" in json.dumps(corpo):
                    return {"items": []}
                if (
                    erro.code not in self.config.status_retry
                    or tentativa + 1 == self.config.tentativas_requisicao
                ):
                    raise RuntimeError(f"Falha YouTube HTTP {erro.code}") from None
            except (URLError, TimeoutError):
                if tentativa + 1 == self.config.tentativas_requisicao:
                    raise RuntimeError("Falha de transporte YouTube") from None
            self.esperar(self.config.espera_retry_segundos * (tentativa + 1))
        raise RuntimeError("Requisição YouTube sem resultado")
