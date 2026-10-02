"""Fusão ponderada de rankings semântico e lexical."""
from documentos_rag.documento_rag import DocumentoRag
from recuperacao_rag.contratos_busca import FiltrosBusca, FonteBusca


class EstrategiaHibrida:
    def __init__(self, semantica: FonteBusca, lexical: FonteBusca, peso_semantico: float,
                 peso_lexical: float, constante_rrf: float) -> None:
        if min(peso_semantico, peso_lexical) < 0 or peso_semantico + peso_lexical <= 0 or constante_rrf <= 0:
            raise ValueError("Pesos e constante de fusão inválidos")
        self.fontes = ((semantica, peso_semantico), (lexical, peso_lexical))
        self.constante_rrf = constante_rrf

    def buscar_documentos(self, pergunta: str, quantidade: int, filtros: FiltrosBusca) -> list[DocumentoRag]:
        pontos: dict[str, float] = {}
        documentos: dict[str, DocumentoRag] = {}
        for fonte, peso in self.fontes:
            vistos: set[str] = set()
            for posicao, documento in enumerate(fonte.buscar_documentos(pergunta, quantidade, filtros), start=1):
                chave = documento.documento_id
                if chave in vistos:
                    continue
                vistos.add(chave)
                documentos[chave] = documento
                pontos[chave] = pontos.get(chave, 0.0) + peso / (self.constante_rrf + posicao)
        return [documentos[chave] for chave in sorted(pontos, key=lambda chave: (-pontos[chave], chave))[:quantidade]]
