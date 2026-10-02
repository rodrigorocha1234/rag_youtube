"""Mensagens controladas sem divulgar exceções de fornecedores."""

import json
import sys
from unittest.mock import patch

import pytest

from configuracao_app.erro_configuracao import ErroConfiguracao
from pipeline_principal.__main__ import executar_comando


@pytest.mark.parametrize(
    "erro", [ErroConfiguracao("arquivo_youtube_ausente"), ValueError("credencial_nao_publicar")]
)
def test_cli_diagnostico_nao_expoe_fornecedor(
    erro: Exception, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["pipeline", "--projeto", "projeto.yaml", "--modelos", "modelos.yaml", "--raiz", "."],
    )
    with patch("pipeline_principal.__main__.CarregadorConfig.carregar_projeto", side_effect=erro):
        assert executar_comando() == 1
    saida = capsys.readouterr().out
    assert "credencial_nao_publicar" not in saida
    dados = json.loads(saida)
    assert dados["estado"] == "falha"
    if isinstance(erro, ErroConfiguracao):
        assert dados["codigo"] == erro.codigo and dados["orientacao"] == erro.orientacao
    else:
        assert set(dados) == {"estado", "tipo"}
