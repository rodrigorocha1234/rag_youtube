"""Resultado auditável da geração."""
from dataclasses import dataclass

from documentos_rag.documento_rag import DocumentoRag


@dataclass(frozen=True)
class RespostaFontes:
    texto: str
    fontes: tuple[DocumentoRag, ...]
    tem_contexto: bool
