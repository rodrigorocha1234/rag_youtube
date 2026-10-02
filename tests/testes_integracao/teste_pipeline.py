"""Fluxo composto com API isolada e persistência real em diretório temporário."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from configuracao_app.carregador_config import CarregadorConfig
from dominio_youtube.comentario_youtube import ComentarioYoutube
from pipeline_principal.execucao_pipeline import ExecucaoPipeline


def test_pipeline_lake_sem_pergunta(tmp_path: Path) -> None:
    projeto = CarregadorConfig.carregar_projeto(Path("configuracao/projeto_rag.yaml"))
    modelos = CarregadorConfig.carregar_modelos(Path("configuracao/modelos_rag.yaml"))
    projeto.mlflow.habilitado = False
    arquivo = tmp_path / projeto.youtube.arquivo_ambiente
    arquivo.write_text("YOUTUBE_API_KEY=segredo_apenas_teste\n")
    instante = datetime.now(timezone.utc)
    registro = ComentarioYoutube(
        canal_id="canal",
        video_id="video",
        comentario_id="id",
        comentario_pai_id=None,
        texto_original=" texto ",
        texto_normalizado="",
        data_publicacao=instante,
        data_atualizacao=instante,
        data_ingestao=instante,
        quantidade_likes=0,
        tipo_documento="comentario",
    )
    with (
        patch.object(ExecucaoPipeline, "preparar_ambiente"),
        patch(
            "pipeline_principal.execucao_pipeline.ColetorComentarios.coletar_canais",
            return_value=[registro],
        ),
        patch("pipeline_principal.execucao_pipeline.construir_servico") as factory,
    ):
        assert ExecucaoPipeline(projeto, modelos, tmp_path).executar_fluxo(None, {}) is None
        docs = factory.call_args.args[2]
        assert docs[0].conteudo == "texto"
        assert docs[0].metadados["comentario_id"] == "id"
    lake = tmp_path / projeto.datalake.diretorio_raiz
    assert list((lake / projeto.datalake.camada_prata).glob("*.jsonl"))
    assert list((lake / projeto.datalake.camada_ouro).glob("*.jsonl"))
    metricas = (tmp_path / projeto.observabilidade.arquivo_metricas).read_text()
    assert "segredo_apenas_teste" not in metricas
    assert 'etapa="ouro"' in metricas


def test_pipeline_vazio_nao_carrega_modelos(tmp_path: Path) -> None:
    projeto = CarregadorConfig.carregar_projeto(Path("configuracao/projeto_rag.yaml"))
    modelos = CarregadorConfig.carregar_modelos(Path("configuracao/modelos_rag.yaml"))
    projeto.mlflow.habilitado = False
    (tmp_path / projeto.youtube.arquivo_ambiente).write_text(
        "YOUTUBE_API_KEY=segredo_apenas_teste\n"
    )
    with (
        patch.object(ExecucaoPipeline, "preparar_ambiente"),
        patch(
            "pipeline_principal.execucao_pipeline.ColetorComentarios.coletar_canais",
            return_value=[],
        ),
        patch("pipeline_principal.execucao_pipeline.construir_servico") as factory,
    ):
        resposta = ExecucaoPipeline(projeto, modelos, tmp_path).executar_fluxo("Pergunta", {})
        assert resposta is not None and not resposta.tem_contexto and not resposta.fontes
        factory.assert_not_called()
