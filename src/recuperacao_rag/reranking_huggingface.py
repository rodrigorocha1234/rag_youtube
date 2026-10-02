"""Adapter do CrossEncoder da Hugging Face."""
from collections.abc import Callable
from importlib import import_module
from typing import cast

import numpy as np

from documentos_rag.documento_rag import DocumentoRag
from recuperacao_rag.contrato_encoder import PontuadorPares


class RerankingHuggingface:
    def __init__(self, modelo: str, dispositivo: str) -> None:
        fabrica = cast(Callable[..., PontuadorPares], getattr(import_module("sentence_transformers"), "CrossEncoder"))
        self.modelo = fabrica(modelo, device=dispositivo)

    def ordenar_documentos(self, pergunta: str, documentos: list[DocumentoRag]) -> list[DocumentoRag]:
        if not documentos:
            return []
        valores = self.modelo.predict([(pergunta, doc.conteudo) for doc in documentos], convert_to_numpy=True)
        pontos = cast(list[float], np.asarray(valores, dtype=float).reshape(-1).tolist())
        if not np.isfinite(pontos).all():
            raise ValueError("Reranker retornou pontuações inválidas")
        return [doc for _, doc in sorted(zip(pontos, documentos, strict=True), key=lambda item: item[0], reverse=True)]
