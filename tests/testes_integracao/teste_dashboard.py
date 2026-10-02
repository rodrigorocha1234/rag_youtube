"""Contrato entre dataset, métricas reais e dashboard provisionável."""

import json
from pathlib import Path

import pytest
import yaml

from observabilidade_app.gerador_dashboard import GeradorDashboard
from observabilidade_app.monitor_operacao import MonitorOperacao


def test_dashboard_referencia_dataset_e_metricas_reais(tmp_path: Path) -> None:
    origem = Path("configuracao/dashboard_rag.yaml")
    config = yaml.safe_load(origem.read_text())
    config["arquivo_saida"] = str(tmp_path / "dashboard.json")
    projeto = yaml.safe_load(Path(config["arquivo_projeto"]).read_text())
    projeto["observabilidade"]["namespace_metricas"] = "namespace_teste"
    arquivo_projeto = tmp_path / "projeto.yaml"
    arquivo_projeto.write_text(yaml.safe_dump(projeto))
    config["arquivo_projeto"] = str(arquivo_projeto)
    arquivo_config = tmp_path / "dashboard.yaml"
    arquivo_config.write_text(yaml.safe_dump(config))
    destino = GeradorDashboard().gerar_arquivo(arquivo_config, Path.cwd())
    dashboard = json.loads(destino.read_text())
    assert dashboard["uid"] == "rag-comentarios-youtube"
    variaveis = {var["name"]: var for var in dashboard["templating"]["list"]}
    assert variaveis["namespace"]["current"]["value"] == "namespace_teste"
    assert variaveis["fonte"]["current"]["value"] == config["fonte_uid"]
    textos = "\n".join(
        painel.get("options", {}).get("content", "") for painel in dashboard["panels"]
    )
    assert "sintéticos" in textos
    assert "Qual dificuldade foi relatada?" in textos and "Qual preço foi citado?" in textos
    assert "não resultados de uma avaliação real" in textos
    assert "__DATASET__" not in destino.read_text()
    monitor = MonitorOperacao("namespace_teste", (0.1, 1.0))
    monitor.registrar_contagem("ouro", 3)
    monitor.registrar_qualidade("mrr", 0.5)
    with monitor.envolver_etapa("ouro"):
        pass
    with pytest.raises(ValueError), monitor.envolver_etapa("youtube"):
        raise ValueError("erro de teste")
    metricas = monitor.exportar_metricas().decode()
    expressoes = [
        alvo["expr"] for painel in dashboard["panels"] for alvo in painel.get("targets", [])
    ]
    for nome in (
        "eventos_total",
        "erros_total",
        "latencia_segundos_sum",
        "latencia_segundos_count",
        "qualidade",
    ):
        assert f"namespace_teste_{nome}" in metricas
        assert any("${namespace}_" + nome in expr for expr in expressoes)
    assert all("rate(" not in expr and "increase(" not in expr for expr in expressoes)
    assert all("vector(0)" not in expr for expr in expressoes)


def test_dashboard_dataset_invalido_preserva_destino(tmp_path: Path) -> None:
    config = yaml.safe_load(Path("configuracao/dashboard_rag.yaml").read_text())
    arquivo_dataset = tmp_path / "dataset.jsonl"
    arquivo_dataset.write_text('{"inputs": {"question": "incompleto"}}\n')
    destino = tmp_path / "dashboard.json"
    destino.write_text("preservar")
    config.update(arquivo_dataset=str(arquivo_dataset), arquivo_saida=str(destino))
    arquivo_config = tmp_path / "config.yaml"
    arquivo_config.write_text(yaml.safe_dump(config))
    with pytest.raises(ValueError):
        GeradorDashboard().gerar_arquivo(arquivo_config, Path.cwd())
    assert destino.read_text() == "preservar"
