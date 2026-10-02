"""Métricas determinísticas calculadas contra evidências versionadas."""
from math import log2


def avaliar_recuperacao(recuperados: list[str], relevantes: set[str]) -> dict[str, float]:
    unicos = list(dict.fromkeys(recuperados))
    acertos = [identificador in relevantes for identificador in unicos]
    recall = sum(acertos) / len(relevantes) if relevantes else 0.0
    mrr = next((1.0 / posicao for posicao, acerto in enumerate(acertos, start=1) if acerto), 0.0)
    dcg = sum(1.0 / log2(posicao + 1) for posicao, acerto in enumerate(acertos, start=1) if acerto)
    ideal = sum(1.0 / log2(posicao + 1) for posicao in range(1, min(len(relevantes), len(unicos)) + 1))
    return {"recall": recall, "mrr": mrr, "ndcg": dcg / ideal if ideal else 0.0,
            "hit_rate": float(bool(sum(acertos)))}
