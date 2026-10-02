"""Critérios locais de contrato; juízes semânticos pertencem ao MLflow GenAI."""
from geracao_resposta.resposta_fontes import RespostaFontes


def avaliar_geracao(resposta: RespostaFontes, evidencias: set[str], resposta_esperada: str) -> dict[str, float]:
    fontes = {doc.documento_id for doc in resposta.fontes}
    return {"fontes_validas": float(bool(fontes) and fontes.issubset(evidencias)),
            "correspondencia_exata": float(resposta.texto.strip().casefold() == resposta_esperada.strip().casefold()),
            "contexto_disponivel": float(resposta.tem_contexto)}
