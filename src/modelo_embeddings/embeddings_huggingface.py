from typing import override

from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings


class EmbeddingsHuggingface(Embeddings):
    def __init__(self, modelo: str, dispositivo: str, normalizar: bool, revisao: str) -> None:
        self.modelo = modelo
        self.revisao = revisao
        self._modelo = HuggingFaceEmbeddings(
            model_name=modelo,
            model_kwargs={"device": dispositivo, "revision": revisao},
            encode_kwargs={"normalize_embeddings": normalizar},
        )

    @override
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._modelo.embed_documents(texts)

    @override
    def embed_query(self, text: str) -> list[float]:
        return self._modelo.embed_query(text)
