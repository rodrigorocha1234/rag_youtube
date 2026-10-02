from pathlib import Path

import pytest
from pydantic import ValidationError

from configuracao_app.carregador_config import CarregadorConfig


def test_scaffold_valido_operacao_rejeitada() -> None:
    projeto = CarregadorConfig.carregar_projeto(Path("configuracao/projeto_rag.yaml"))
    modelos = CarregadorConfig.carregar_modelos(Path("configuracao/modelos_rag.yaml"))
    projeto.youtube.ids_canais = ["UC_CANAL_PLACEHOLDER"]
    with pytest.raises(ValueError, match="placeholder"):
        CarregadorConfig.validar_operacao(projeto, modelos)


def test_rejeita_chave_desconhecida() -> None:
    projeto = CarregadorConfig.carregar_projeto(Path("configuracao/projeto_rag.yaml"))
    dados = projeto.model_dump()
    dados["desconhecida"] = True
    with pytest.raises(ValidationError):
        type(projeto).model_validate(dados)


def test_segredo_arquivo_separado(tmp_path: Path) -> None:
    projeto = CarregadorConfig.carregar_projeto(Path("configuracao/projeto_rag.yaml"))
    (tmp_path / projeto.youtube.arquivo_ambiente).write_text("YOUTUBE_API_KEY=valor_teste\n")
    segredo = CarregadorConfig.carregar_segredo(projeto, tmp_path)
    assert "valor_teste" not in repr(segredo)
    assert segredo.get_secret_value() == "valor_teste"


@pytest.mark.parametrize(
    "campo,valor",
    [
        ("youtube", {"ids_canais": []}),
        ("youtube", {"timezone": "zona/inexistente"}),
        ("observabilidade", {"buckets_latencia": [1, 0.5]}),
        ("vetor", {"tabela": "tabela;drop"}),
        ("rag", {"peso_semantico": 0, "peso_lexical": 0}),
    ],
)
def test_configuracao_rejeita_contratos_invalidos(campo: str, valor: dict[str, object]) -> None:
    from configuracao_app.modelos_config import ProjetoRagConfig

    projeto = CarregadorConfig.carregar_projeto(Path("configuracao/projeto_rag.yaml"))
    dados: dict[str, object] = projeto.model_dump()
    secao = dados[campo]
    assert isinstance(secao, dict)
    secao.update(valor)
    with pytest.raises(ValidationError):
        ProjetoRagConfig.model_validate(dados)


def test_prompt_rejeita_placeholder_inesperado() -> None:
    from configuracao_app.modelos_config import ModelosRagConfig

    modelos = CarregadorConfig.carregar_modelos(Path("configuracao/modelos_rag.yaml"))
    dados = modelos.model_dump()
    dados["geracao"]["prompt_contexto"] = "{pergunta} {contexto} {segredo}"
    with pytest.raises(ValidationError):
        ModelosRagConfig.model_validate(dados)


def test_segredo_ausente_diagnostico_controlado(tmp_path: Path) -> None:
    from configuracao_app.erro_configuracao import ErroConfiguracao

    projeto = CarregadorConfig.carregar_projeto(Path("configuracao/projeto_rag.yaml"))
    with pytest.raises(ErroConfiguracao) as capturado:
        CarregadorConfig.carregar_segredo(projeto, tmp_path)
    assert capturado.value.codigo == "arquivo_youtube_ausente"


@pytest.mark.parametrize(
    "conteudo", ["", "YOUTUBE_API_KEY=", "YOUTUBE_API_KEY=COLOQUE_SUA_CHAVE_AQUI"]
)
def test_segredo_invalido_diagnostico_controlado(tmp_path: Path, conteudo: str) -> None:
    from configuracao_app.erro_configuracao import ErroConfiguracao

    projeto = CarregadorConfig.carregar_projeto(Path("configuracao/projeto_rag.yaml"))
    (tmp_path / projeto.youtube.arquivo_ambiente).write_text(conteudo)
    with pytest.raises(ErroConfiguracao) as capturado:
        CarregadorConfig.carregar_segredo(projeto, tmp_path)
    assert capturado.value.codigo == "chave_youtube_invalida"
