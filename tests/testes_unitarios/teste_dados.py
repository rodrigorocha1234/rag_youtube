from datetime import datetime, timezone
from email.message import Message
from pathlib import Path

import pytest

from coleta_youtube.coletor_comentarios import ColetorComentarios
from configuracao_app.carregador_config import CarregadorConfig
from documentos_rag.construtor_documentos import ConstrutorDocumentos
from dominio_youtube.comentario_youtube import ComentarioYoutube
from dominio_youtube.tipos_json import ObjetoJson
from tratamento_texto.normalizador_texto import NormalizadorTexto


class ClienteFake:
    def __init__(self) -> None:
        self.chamadas: list[dict[str, str]] = []

    def consultar_recurso(self, recurso: str, parametros: dict[str, str]) -> ObjetoJson:
        self.chamadas.append(parametros)
        if "pageToken" not in parametros:
            return {"items": [{"id": "primeiro"}], "nextPageToken": "seguinte"}
        return {"items": [{"id": "segundo"}]}


def test_paginacao_preserva_bronze() -> None:
    config = CarregadorConfig.carregar_projeto(Path("configuracao/projeto_rag.yaml")).youtube
    bruto: list[ObjetoJson] = []
    cliente = ClienteFake()
    coletor = ColetorComentarios(
        config, cliente, lambda recurso, payload, instante: bruto.append(payload)
    )
    itens = list(coletor.paginar_recurso("comments", {}, datetime.now(timezone.utc)))
    assert len(itens) == len(bruto) == 2
    assert cliente.chamadas[1]["pageToken"] == "seguinte"


def test_janela_exata_timezone() -> None:
    config = CarregadorConfig.carregar_projeto(Path("configuracao/projeto_rag.yaml")).youtube
    coletor = ColetorComentarios(config, ClienteFake(), lambda recurso, payload, instante: None)
    instante = datetime.fromisoformat("2026-10-01T12:00:00+00:00")
    assert coletor.incluir_publicacao(datetime.fromisoformat("2026-09-30T02:00:00+00:00"), instante)
    assert not coletor.incluir_publicacao(
        datetime.fromisoformat("2026-09-30T12:00:00+00:00"), instante
    )


def test_normalizacao_dedup_proveniencia() -> None:
    instante = datetime.now(timezone.utc)
    registro = ComentarioYoutube(
        canal_id="canal",
        video_id="video",
        comentario_id="comentario",
        comentario_pai_id=None,
        texto_original="  <b>Olá</b>   mundo ",
        texto_normalizado="",
        data_publicacao=instante,
        data_atualizacao=instante,
        quantidade_likes=3,
        tipo_documento="comentario",
        data_ingestao=instante,
    )
    prata = NormalizadorTexto().normalizar_registros([registro, registro])
    assert len(prata) == 1
    assert prata[0].texto_normalizado == "Olá mundo"
    ouro = ConstrutorDocumentos().construir_documentos(prata)
    assert ouro[0].metadados["video_id"] == "video"
    assert ouro[0].documento_id == "comentario"


def test_quota_falha_antes_da_rede() -> None:
    import pytest
    from pydantic import SecretStr

    from coleta_youtube.cliente_youtube import ClienteYoutube

    config = CarregadorConfig.carregar_projeto(Path("configuracao/projeto_rag.yaml")).youtube
    cliente = ClienteYoutube(config, SecretStr("teste"))
    cliente.quota_consumida = config.quota_maxima
    with pytest.raises(RuntimeError, match="Quota"):
        cliente.consultar_recurso("channels", {})


def test_limite_por_recurso_e_token_repetido() -> None:
    import pytest

    config = CarregadorConfig.carregar_projeto(Path("configuracao/projeto_rag.yaml")).youtube
    cliente = ClienteFake()
    coletor = ColetorComentarios(config, cliente, lambda recurso, payload, instante: None)
    list(coletor.paginar_recurso("channels", {}, datetime.now(timezone.utc)))
    assert cliente.chamadas[0]["maxResults"] == "50"

    class ClienteRepetido:
        def consultar_recurso(self, recurso: str, parametros: dict[str, str]) -> ObjetoJson:
            return {"items": [], "nextPageToken": "repetido"}

    coletor = ColetorComentarios(config, ClienteRepetido(), lambda recurso, payload, instante: None)
    with pytest.raises(ValueError, match="repetido"):
        list(coletor.paginar_recurso("channels", {}, datetime.now(timezone.utc)))


def test_http_retry_comments_desabilitados(monkeypatch: pytest.MonkeyPatch) -> None:
    import io
    from urllib.error import HTTPError

    from pydantic import SecretStr

    from coleta_youtube.cliente_youtube import ClienteYoutube

    config = CarregadorConfig.carregar_projeto(Path("configuracao/projeto_rag.yaml")).youtube
    tentativas: list[str] = []
    esperas: list[float] = []

    def consultar(url: str, timeout: float) -> object:
        tentativas.append(url)
        corpo = (
            b'{"error":{"errors":[{"reason":"commentsDisabled"}]}}'
            if len(tentativas) > 1
            else b"not-json"
        )
        raise HTTPError(
            url, 403 if len(tentativas) > 1 else 503, "erro", Message(), io.BytesIO(corpo)
        )

    monkeypatch.setattr("coleta_youtube.cliente_youtube.urlopen", consultar)
    cliente = ClienteYoutube(config, SecretStr("segredo"), esperas.append)
    assert cliente.consultar_recurso("commentThreads", {}) == {"items": []}
    assert len(tentativas) == 2
    assert cliente.quota_consumida == 2 * config.custo_requisicao
    assert esperas == [config.espera_retry_segundos]


def test_http_falha_nao_expoe_segredo(monkeypatch: pytest.MonkeyPatch) -> None:
    import io
    from urllib.error import HTTPError

    from pydantic import SecretStr

    from coleta_youtube.cliente_youtube import ClienteYoutube

    config = CarregadorConfig.carregar_projeto(Path("configuracao/projeto_rag.yaml")).youtube

    def consultar(url: str, timeout: float) -> object:
        raise HTTPError(url, 401, "segredo_sensivel", Message(), io.BytesIO(b"{}"))

    monkeypatch.setattr("coleta_youtube.cliente_youtube.urlopen", consultar)
    with pytest.raises(RuntimeError) as capturado:
        ClienteYoutube(config, SecretStr("segredo_sensivel")).consultar_recurso("channels", {})
    assert "segredo_sensivel" not in str(capturado.value)
    assert capturado.value.__suppress_context__


def test_canais_com_respostas_completas_e_lake(tmp_path: Path) -> None:
    import json

    from armazenamento_lake.repositorio_lake import RepositorioLake

    projeto = CarregadorConfig.carregar_projeto(Path("configuracao/projeto_rag.yaml"))
    projeto.youtube.ids_canais = ["canal_a", "canal_b"]
    instante = datetime.fromisoformat("2026-10-01T12:00:00+00:00")

    def comentario(identificador: str, pai: str | None = None) -> ObjetoJson:
        trecho: ObjetoJson = {
            "textOriginal": "conteudo",
            "publishedAt": "2026-09-29T12:00:00Z",
            "updatedAt": "2026-09-29T12:00:00Z",
            "likeCount": 1,
        }
        if pai:
            trecho["parentId"] = pai
        return {"id": identificador, "snippet": trecho}

    class ApiCompleta:
        def consultar_recurso(self, recurso: str, parametros: dict[str, str]) -> ObjetoJson:
            if recurso == "channels":
                return {
                    "items": [
                        {"contentDetails": {"relatedPlaylists": {"uploads": parametros["id"]}}}
                    ]
                }
            if recurso == "playlistItems":
                return {
                    "items": [
                        {
                            "contentDetails": {
                                "videoId": parametros["playlistId"],
                                "videoPublishedAt": "2026-09-29T12:00:00Z",
                            }
                        }
                    ]
                }
            if recurso == "commentThreads":
                return {
                    "items": [
                        {
                            "snippet": {
                                "topLevelComment": comentario(parametros["videoId"]),
                                "totalReplyCount": 2,
                            }
                        }
                    ]
                }
            pai = parametros["parentId"]
            if "pageToken" not in parametros:
                return {"items": [comentario(pai + "_r1", pai)], "nextPageToken": "pagina2"}
            return {"items": [comentario(pai + "_r2", pai)]}

    lake = RepositorioLake(projeto.datalake, tmp_path)
    registros = ColetorComentarios(
        projeto.youtube, ApiCompleta(), lake.salvar_bronze
    ).coletar_canais(instante)
    assert len(registros) == 6
    assert {item.canal_id for item in registros} == {"canal_a", "canal_b"}
    assert sum(item.tipo_documento == "resposta" for item in registros) == 4
    prata = NormalizadorTexto().normalizar_registros(registros)
    caminho_prata = lake.salvar_prata(prata)
    ouro = ConstrutorDocumentos().construir_documentos(prata)
    caminho_ouro = lake.salvar_ouro(ouro)
    assert len(caminho_prata.read_text().splitlines()) == 6
    assert (
        json.loads(caminho_ouro.read_text().splitlines()[0])["metadados"]["canal_id"]
        in projeto.youtube.ids_canais
    )
    bronze = list(
        (tmp_path / projeto.datalake.diretorio_raiz / projeto.datalake.camada_bronze).glob(
            "*.jsonl"
        )
    )
    assert len(bronze) == 10
    assert "payload" in json.loads(bronze[0].read_text())
