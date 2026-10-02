"""Contrato pyfunc: consulta sem ingestão e recusa sem documentos."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import yaml
from mlflow.pyfunc.model import PythonModelContext

from configuracao_app.carregador_config import CarregadorConfig
from documentos_rag.documento_rag import DocumentoRag
from geracao_resposta.resposta_fontes import RespostaFontes
from integracao_mlflow.configuracao_serving import ConfiguracaoServing
from integracao_mlflow.modelo_consulta import ModeloConsulta


def preparar_contexto(
    tmp_path: Path, documentos: list[DocumentoRag]
) -> tuple[ModeloConsulta, PythonModelContext]:
    config = ConfiguracaoServing.model_validate(
        yaml.safe_load(Path("configuracao/servico_rag.yaml").read_text())
    )
    config.arquivo_metricas = str(tmp_path / "metricas.prom")
    projeto = CarregadorConfig.carregar_projeto(Path(config.arquivo_projeto))
    projeto.mlflow.habilitado = False
    arquivo_projeto = tmp_path / "projeto.yaml"
    arquivo_projeto.write_text(yaml.safe_dump(projeto.model_dump(mode="json")))
    ouro = tmp_path / "ouro.jsonl"
    ouro.write_text("\n".join(doc.model_dump_json() for doc in documentos))
    context = PythonModelContext(
        {
            config.artefato_projeto: str(arquivo_projeto),
            config.artefato_modelos: config.arquivo_modelos,
            config.artefato_documentos: str(ouro),
        },
        {},
    )
    return ModeloConsulta(config), context


def test_serving_vazio_nao_coleta_ou_carrega_hf(tmp_path: Path) -> None:
    modelo, context = preparar_contexto(tmp_path, [])
    with patch("integracao_mlflow.modelo_consulta.construir_servico") as factory:
        modelo.load_context(context)
        resultados = modelo.predict(context, [{"pergunta": "Qual preço foi citado?"}])
    factory.assert_not_called()
    assert resultados == [{"resposta": modelo.modelos.geracao.prompt_sem_contexto, "fontes": []}]
    assert 'etapa="respostas_servidas"' in Path(modelo.config.arquivo_metricas).read_text()


def test_serving_filtros_lote_e_sanitizacao(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from unittest.mock import Mock

    monkeypatch.setenv("POSTGRES_CONNECTION_STRING", "conexao_secreta")
    doc = DocumentoRag(
        documento_id="comentario", conteudo="evidência", metadados={"canal_id": "canal"}
    )
    modelo, context = preparar_contexto(tmp_path, [doc])
    servico = Mock()
    servico.responder_pergunta.return_value = RespostaFontes(
        "Resposta conexao_secreta", (doc,), True
    )
    with patch(
        "integracao_mlflow.modelo_consulta.construir_servico",
        return_value=SimpleNamespace(servico=servico),
    ) as factory:
        modelo.load_context(context)
    assert factory.call_args.kwargs == {"indexar": False}
    resultados = modelo.predict(
        context,
        [{"pergunta": "Dúvida?", "canal_id": "canal", "video_id": "video"}, {"pergunta": "Outra?"}],
    )
    assert len(resultados) == 2
    assert resultados[0]["resposta"] == "Resposta [REDACTED]"
    assert servico.responder_pergunta.call_args_list[0].args == (
        "Dúvida?",
        {"canal_id": "canal", "video_id": "video"},
    )
    assert "conexao_secreta" not in Path(modelo.config.arquivo_metricas).read_text()


def test_serving_rejeita_pergunta_vazia_antes_do_lote(tmp_path: Path) -> None:
    modelo, context = preparar_contexto(tmp_path, [])
    modelo.load_context(context)
    with pytest.raises(ValueError):
        modelo.predict(context, [{"pergunta": ""}])


def test_factory_consulta_preserva_indice(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import Mock

    from integracao_mlflow.tracador_mlflow import TracadorMlflow
    from observabilidade_app.monitor_operacao import MonitorOperacao
    from recuperacao_rag.fabrica_servico import construir_servico

    monkeypatch.setenv("POSTGRES_CONNECTION_STRING", "conexao_de_teste")
    config = ConfiguracaoServing.model_validate(
        yaml.safe_load(Path("configuracao/servico_rag.yaml").read_text())
    )
    projeto = CarregadorConfig.carregar_projeto(Path(config.arquivo_projeto))
    modelos = CarregadorConfig.carregar_modelos(Path(config.arquivo_modelos))
    monitor = MonitorOperacao("serving_teste", (0.1, 1.0))
    tracador = TracadorMlflow(False, None, "teste")
    banco = Mock()
    with (
        patch("recuperacao_rag.fabrica_servico.criar_embeddings"),
        patch(
            "recuperacao_rag.fabrica_servico.RepositorioPgvector.criar_repositorio",
            return_value=banco,
        ) as abrir,
        patch("recuperacao_rag.fabrica_servico.GeradorHuggingface"),
        patch("recuperacao_rag.fabrica_servico.RerankingHuggingface"),
    ):
        construir_servico(projeto, modelos, [], monitor, tracador, indexar=False)
    assert abrir.call_args.args[-1] is False
    banco.salvar_documentos.assert_not_called()
