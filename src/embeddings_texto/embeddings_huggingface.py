"""Factory do adapter LangChain para embeddings Hugging Face."""
from langchain_core.embeddings import Embeddings


def criar_embeddings(modelo: str, dispositivo: str, normalizar: bool, tamanho_lote: int) -> Embeddings:
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(model_name=modelo, model_kwargs={"device": dispositivo},
                                 encode_kwargs={"normalize_embeddings": normalizar, "batch_size": tamanho_lote})
