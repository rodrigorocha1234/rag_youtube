from collections.abc import Sequence
from dataclasses import replace
from typing import cast

from sentence_transformers import CrossEncoder

from dominio_youtube.contratos_rag import DocumentoRag


class RerankingHuggingface:
    def __init__(self, modelo: str, dispositivo: str, revisao: str) -> None:
        self._modelo = CrossEncoder(modelo, device=dispositivo, revision=revisao)

    def reordenar_documentos(
        self, pergunta: str, documentos: Sequence[DocumentoRag]
    ) -> list[DocumentoRag]:
        if not documentos:
            return []
        scores = cast(
            list[float],
            self._modelo.predict([(pergunta, documento.texto) for documento in documentos]).tolist(),
        )
        classificados = [
            replace(documento, score=float(score))
            for documento, score in zip(documentos, scores, strict=True)
        ]
        return sorted(classificados, key=lambda documento: documento.score or 0.0, reverse=True)
