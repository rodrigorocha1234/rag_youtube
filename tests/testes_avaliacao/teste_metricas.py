import pytest

from avaliacao_rag.metricas_recuperacao import avaliar_recuperacao


def test_metricas_penalizam_ranking_ruim() -> None:
    metricas = avaliar_recuperacao(["irrelevante", "a", "a"], {"a", "b"})
    assert metricas["recall"] == 0.5
    assert metricas["mrr"] == 0.5
    assert 0 < metricas["ndcg"] < 1
    assert metricas["hit_rate"] == 1
    assert avaliar_recuperacao([], {"a"})["mrr"] == 0
    assert avaliar_recuperacao(["a"], {"a"})["ndcg"] == pytest.approx(1)
