from datetime import UTC, datetime, timedelta

from cliente_youtube.cliente_youtube import ClienteYoutube
from dominio_youtube.contratos_ingestao import (
    VideoYoutube, itens_json, objeto_json, texto_json,
)


class DescobertaVideos:
    def __init__(self, cliente: ClienteYoutube) -> None:
        self.cliente = cliente

    def descobrir(
        self, id_canal: str, dias_publicacao_atras: int, agora: datetime | None = None,
    ) -> list[VideoYoutube]:
        if dias_publicacao_atras < 0:
            raise ValueError("Janela de publicação negativa")
        limite = (agora or datetime.now(UTC)) - timedelta(days=dias_publicacao_atras)
        canais = self.cliente.requisitar("channels", {"part": "contentDetails,snippet", "id": id_canal})
        itens = itens_json(canais)
        if not itens:
            raise ValueError("Canal não encontrado")
        canal = itens[0]
        detalhes = objeto_json(canal["contentDetails"])
        playlist = texto_json(objeto_json(detalhes["relatedPlaylists"])["uploads"])
        titulo_canal = texto_json(objeto_json(canal.get("snippet", {})).get("title", ""))
        videos: dict[str, VideoYoutube] = {}
        for pagina in self.cliente.paginar(
            "playlistItems", {"part": "snippet,contentDetails", "playlistId": playlist},
        ):
            for item in itens_json(pagina):
                snippet = objeto_json(item["snippet"])
                detalhes_item = objeto_json(item["contentDetails"])
                publicada = detalhes_item.get("videoPublishedAt", snippet.get("publishedAt"))
                data = datetime.fromisoformat(texto_json(publicada).replace("Z", "+00:00"))
                if data >= limite:
                    id_video = texto_json(detalhes_item["videoId"])
                    videos[id_video] = VideoYoutube(
                        id_video, id_canal, texto_json(snippet["title"]), data, titulo_canal,
                    )
        return list(videos.values())
