import hashlib
import json
from datetime import UTC, datetime

from pydantic import JsonValue

from armazenamento_s3.repositorio_s3 import RepositorioS3
from dominio_youtube.contratos_ingestao import VideoYoutube


class ProcessadorBronze:
    def __init__(self, repositorio: RepositorioS3, prefixo: str) -> None:
        self.repositorio = repositorio
        self.prefixo = prefixo.rstrip("/")

    def salvar(self, video: VideoYoutube, endpoint: str, pagina: dict[str, JsonValue]) -> str:
        data = datetime.now(UTC).date().isoformat()
        resumo = hashlib.sha256(json.dumps(pagina, sort_keys=True).encode()).hexdigest()
        chave = (
            f"{self.prefixo}/canal={video.id_canal}/video={video.id_video}/data={data}"
            f"/endpoint={endpoint}/{resumo}.json"
        )
        self.repositorio.salvar_json(chave, pagina)
        return chave
