"""Persistência atômica das camadas sem expor credenciais."""

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from configuracao_app.modelos_config import DatalakeConfig
from documentos_rag.documento_rag import DocumentoRag
from dominio_youtube.comentario_youtube import ComentarioYoutube
from dominio_youtube.tipos_json import ObjetoJson


class RepositorioLake:
    def __init__(self, config: DatalakeConfig, raiz: Path) -> None:
        self.config = config
        self.raiz = raiz / config.diretorio_raiz

    def escrever_registros(self, camada: str, registros: list[str]) -> Path:
        diretorio = self.raiz / camada
        diretorio.mkdir(parents=True, exist_ok=True)
        destino = diretorio / f"{uuid4().hex}.jsonl"
        temporario = destino.with_suffix(".tmp")
        temporario.write_text("\n".join(registros) + "\n", encoding="utf-8")
        temporario.replace(destino)
        return destino

    def salvar_bronze(self, recurso: str, payload: ObjetoJson, instante: datetime) -> Path:
        registro = {"recurso": recurso, "data_ingestao": instante.isoformat(), "payload": payload}
        return self.escrever_registros(
            self.config.camada_bronze, [json.dumps(registro, ensure_ascii=False)]
        )

    def salvar_prata(self, registros: list[ComentarioYoutube]) -> Path:
        return self.escrever_registros(
            self.config.camada_prata, [item.model_dump_json() for item in registros]
        )

    def salvar_ouro(self, documentos: list[DocumentoRag]) -> Path:
        return self.escrever_registros(
            self.config.camada_ouro, [item.model_dump_json() for item in documentos]
        )
