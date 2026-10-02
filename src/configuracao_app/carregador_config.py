"""Carregamento separado da validação para execução externa."""

from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from dotenv import dotenv_values
from pydantic import SecretStr

from configuracao_app.erro_configuracao import ErroConfiguracao
from configuracao_app.modelos_config import ModelosRagConfig, ProjetoRagConfig


class CarregadorConfig:
    @staticmethod
    def carregar_projeto(caminho: Path) -> ProjetoRagConfig:
        return ProjetoRagConfig.model_validate(yaml.safe_load(caminho.read_text()))

    @staticmethod
    def carregar_modelos(caminho: Path) -> ModelosRagConfig:
        return ModelosRagConfig.model_validate(yaml.safe_load(caminho.read_text()))

    @staticmethod
    def carregar_segredo(config: ProjetoRagConfig, raiz: Path) -> SecretStr:
        arquivo = raiz / config.youtube.arquivo_ambiente
        if not arquivo.is_file():
            raise ErroConfiguracao("arquivo_youtube_ausente")
        valores = dotenv_values(arquivo)
        segredo = valores.get(config.youtube.segredo_ambiente)
        if (
            not segredo
            or segredo.startswith("CONFIGURE_")
            or segredo in {"sua_chave_aqui", "COLOQUE_SUA_CHAVE_AQUI"}
        ):
            raise ErroConfiguracao("chave_youtube_invalida")
        return SecretStr(segredo)

    @staticmethod
    def validar_operacao(projeto: ProjetoRagConfig, modelos: ModelosRagConfig) -> None:
        ZoneInfo(projeto.youtube.timezone)
        if projeto.rag.reranking_habilitado != modelos.reranking.habilitado:
            raise ValueError("Flags de reranking inconsistentes")
        campos = [*projeto.youtube.ids_canais, modelos.embeddings.modelo, modelos.geracao.modelo]
        if modelos.reranking.habilitado:
            campos.append(modelos.reranking.modelo)
        if not projeto.youtube.ids_canais or any(
            not campo or campo.startswith(("CONFIGURE_", "UC_CANAL_")) for campo in campos
        ):
            raise ValueError("Configuração operacional contém placeholders ou canais ausentes")
