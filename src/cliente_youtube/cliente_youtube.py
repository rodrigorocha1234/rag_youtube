from collections.abc import Callable, Iterator
from time import sleep

import httpx
from pydantic import JsonValue

from dominio_youtube.contratos_ingestao import ADAPTADOR_JSON, objeto_json, texto_json


class ErroYoutube(RuntimeError):
    def __init__(self, motivo: str, status: int = 0) -> None:
        self.motivo = motivo
        self.status = status
        super().__init__(f"Falha YouTube: {motivo} (status {status})")


class ClienteYoutube:
    def __init__(
        self, cliente: httpx.Client, chave_api: str,
        url_base: str = "https://www.googleapis.com/youtube/v3", tamanho_pagina: int = 100,
        tentativas: int = 3, quota_maxima: int = 10000,
        esperar: Callable[[float], None] = sleep, atraso_base: float = 1.0,
    ) -> None:
        if not chave_api or not 1 <= tamanho_pagina <= 100 or tentativas < 1 or quota_maxima < 1:
            raise ValueError("Configuração YouTube inválida")
        self.cliente = cliente
        self.chave_api = chave_api
        self.url_base = url_base.rstrip("/")
        self.tamanho_pagina = tamanho_pagina
        self.tentativas = tentativas
        self.quota_maxima = quota_maxima
        self.quota_consumida = 0
        self.esperar = esperar
        self.atraso_base = atraso_base

    def requisitar(self, endpoint: str, parametros: dict[str, str]) -> dict[str, JsonValue]:
        consulta = {**parametros, "key": self.chave_api}
        for tentativa in range(self.tentativas):
            if self.quota_consumida >= self.quota_maxima:
                raise ErroYoutube("quotaLocalEsgotada")
            self.quota_consumida += 1
            try:
                resposta = self.cliente.get(f"{self.url_base}/{endpoint}", params=consulta)
            except httpx.TransportError:
                if tentativa + 1 == self.tentativas:
                    raise ErroYoutube("transporte") from None
                self.esperar(self.atraso_base * 2**tentativa)
                continue
            pagina = objeto_json(ADAPTADOR_JSON.validate_json(resposta.content))
            if resposta.is_success:
                return pagina
            motivo = "erroHttp"
            erro = pagina.get("error")
            if isinstance(erro, dict):
                erros = erro.get("errors")
                if isinstance(erros, list) and erros:
                    primeiro = objeto_json(erros[0])
                    motivo = texto_json(primeiro.get("reason", motivo))
            repetivel = resposta.status_code == 429 or resposta.status_code >= 500
            repetivel = repetivel or motivo in {"rateLimitExceeded", "userRateLimitExceeded"}
            if not repetivel or tentativa + 1 == self.tentativas:
                raise ErroYoutube(motivo, resposta.status_code)
            self.esperar(self.atraso_base * 2**tentativa)
        raise ErroYoutube("tentativasEsgotadas")

    def paginar(self, endpoint: str, parametros: dict[str, str]) -> Iterator[dict[str, JsonValue]]:
        consulta = {**parametros, "maxResults": str(self.tamanho_pagina)}
        tokens: set[str] = set()
        while True:
            pagina = self.requisitar(endpoint, consulta)
            yield pagina
            token = pagina.get("nextPageToken")
            if not token:
                return
            proximo = texto_json(token)
            if proximo in tokens:
                raise ErroYoutube("paginacaoCircular")
            tokens.add(proximo)
            consulta["pageToken"] = proximo
