"""Erro controlado de configuração, sem incluir valores de credenciais."""

from typing import Literal


class ErroConfiguracao(ValueError):
    def __init__(
        self, codigo: Literal["arquivo_youtube_ausente", "chave_youtube_invalida"]
    ) -> None:
        self.codigo = codigo
        orientacoes = {
            "arquivo_youtube_ausente": "Crie o arquivo definido em youtube.arquivo_ambiente a partir de youtube.env.example e configure YOUTUBE_API_KEY localmente.",
            "chave_youtube_invalida": "Configure YOUTUBE_API_KEY sem placeholder no arquivo definido em youtube.arquivo_ambiente.",
        }
        self.orientacao = orientacoes[codigo]
        super().__init__(self.orientacao)
