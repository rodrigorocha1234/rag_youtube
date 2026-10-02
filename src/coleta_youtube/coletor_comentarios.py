"""Coleta paginada de uploads, comentários e respostas."""

from collections.abc import Callable, Iterator
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from coleta_youtube.contrato_youtube import ConsultaYoutube
from configuracao_app.modelos_config import YoutubeConfig
from dominio_youtube.comentario_youtube import ComentarioYoutube
from dominio_youtube.tipos_json import ObjetoJson, obter_objeto, obter_texto


class ColetorComentarios:
    def __init__(
        self,
        config: YoutubeConfig,
        cliente: ConsultaYoutube,
        salvar_bruto: Callable[[str, ObjetoJson, datetime], object],
    ) -> None:
        self.config = config
        self.cliente = cliente
        self.salvar_bruto = salvar_bruto

    def paginar_recurso(
        self, recurso: str, parametros: dict[str, str], instante: datetime
    ) -> Iterator[ObjetoJson]:
        token = ""
        tokens_vistos: set[str] = set()
        limite = min(self.config.max_resultados_pagina, self.config.limites_paginas[recurso])
        while True:
            pagina = self.cliente.consultar_recurso(
                recurso,
                {
                    **parametros,
                    "maxResults": str(limite),
                    **({"pageToken": token} if token else {}),
                },
            )
            self.salvar_bruto(recurso, pagina, instante)
            itens = pagina.get("items", [])
            if not isinstance(itens, list):
                raise ValueError("Lista de itens YouTube inválida")
            for item in itens:
                yield obter_objeto(item)
            seguinte = pagina.get("nextPageToken")
            if not seguinte:
                break
            token = obter_texto(seguinte)
            if token in tokens_vistos:
                raise ValueError("Token de paginação YouTube repetido")
            tokens_vistos.add(token)

    def incluir_publicacao(self, publicada: datetime, instante: datetime) -> bool:
        zona = ZoneInfo(self.config.timezone)
        data_alvo = instante.astimezone(zona).date() - timedelta(
            days=self.config.dias_publicacao_atras
        )
        data_video = publicada.astimezone(zona).date()
        if self.config.modo_janela_publicacao == "dia_exato":
            return data_video == data_alvo
        return data_alvo <= data_video <= instante.astimezone(zona).date()

    def converter_comentario(
        self, objeto: ObjetoJson, canal: str, video: str, instante: datetime
    ) -> ComentarioYoutube:
        trecho = obter_objeto(objeto["snippet"])
        pai = trecho.get("parentId")
        texto = trecho.get("textOriginal", trecho.get("textDisplay"))
        likes = trecho.get("likeCount")
        if not isinstance(likes, int):
            raise ValueError("Contagem de likes inválida")
        return ComentarioYoutube(
            canal_id=canal,
            video_id=video,
            comentario_id=obter_texto(objeto["id"]),
            comentario_pai_id=obter_texto(pai) if pai else None,
            texto_original=obter_texto(texto),
            texto_normalizado="",
            data_publicacao=datetime.fromisoformat(obter_texto(trecho["publishedAt"])),
            data_atualizacao=datetime.fromisoformat(obter_texto(trecho["updatedAt"])),
            quantidade_likes=likes,
            tipo_documento="resposta" if pai else "comentario",
            data_ingestao=instante,
        )

    def coletar_video(
        self, canal: str, video: str, instante: datetime
    ) -> Iterator[ComentarioYoutube]:
        for thread in self.paginar_recurso(
            "commentThreads",
            {"part": "snippet", "videoId": video, "textFormat": "plainText"},
            instante,
        ):
            trecho = obter_objeto(thread["snippet"])
            comentario = obter_objeto(trecho["topLevelComment"])
            registro = self.converter_comentario(comentario, canal, video, instante)
            yield registro
            if self.config.incluir_respostas and trecho.get("totalReplyCount", 0):
                for resposta in self.paginar_recurso(
                    "comments",
                    {
                        "part": "snippet",
                        "parentId": registro.comentario_id,
                        "textFormat": "plainText",
                    },
                    instante,
                ):
                    yield self.converter_comentario(resposta, canal, video, instante)

    def coletar_canais(self, instante: datetime | None = None) -> list[ComentarioYoutube]:
        agora = instante or datetime.now(timezone.utc)
        registros: list[ComentarioYoutube] = []
        for canal in self.config.ids_canais:
            for objeto in self.paginar_recurso(
                "channels", {"part": "contentDetails", "id": canal}, agora
            ):
                detalhes = obter_objeto(objeto["contentDetails"])
                playlists = obter_objeto(detalhes["relatedPlaylists"])
                uploads = obter_texto(playlists["uploads"])
                for item in self.paginar_recurso(
                    "playlistItems", {"part": "contentDetails", "playlistId": uploads}, agora
                ):
                    dados = obter_objeto(item["contentDetails"])
                    publicada = datetime.fromisoformat(obter_texto(dados["videoPublishedAt"]))
                    if self.incluir_publicacao(publicada, agora):
                        registros.extend(
                            self.coletar_video(canal, obter_texto(dados["videoId"]), agora)
                        )
        return registros
