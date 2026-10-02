"""Gera JSON provisionável pelo Grafana a partir de YAML e dataset local."""

import argparse
import json
from html import escape
from pathlib import Path

import yaml

from configuracao_app.carregador_config import CarregadorConfig
from dominio_youtube.tipos_json import ObjetoJson, ValorJson, obter_objeto, validar_json
from integracao_mlflow.configuracao_serving import ConfiguracaoServing
from observabilidade_app.configuracao_dashboard import ConfiguracaoDashboard, ExemploAvaliacao


class GeradorDashboard:
    def gerar_arquivo(self, configuracao: Path, raiz: Path) -> Path:
        config = ConfiguracaoDashboard.model_validate(yaml.safe_load(configuracao.read_text()))
        projeto = CarregadorConfig.carregar_projeto(raiz / config.arquivo_projeto)
        serving = ConfiguracaoServing.model_validate(
            yaml.safe_load((raiz / config.arquivo_serving).read_text())
        )
        dataset = raiz / config.arquivo_dataset
        exemplos = [
            ExemploAvaliacao.model_validate_json(linha)
            for linha in dataset.read_text().splitlines()
            if linha.strip()
        ]
        if not exemplos:
            raise ValueError("Dataset de referência vazio")
        linhas = ["| Pergunta | Resposta esperada | Evidências |", "|---|---|---|"]
        for exemplo in exemplos:
            campos = (
                exemplo.inputs.question,
                exemplo.expectations.expected_response,
                ", ".join(exemplo.expectations.documentos_relevantes) or "Sem contexto",
            )
            linhas.append(
                "| "
                + " | ".join(
                    escape(campo).replace("|", "&#124;").replace("\n", " ") for campo in campos
                )
                + " |"
            )
        substituicoes = {
            "__NAMESPACE__": projeto.observabilidade.namespace_metricas,
            "__NAMESPACE_SERVING__": serving.namespace_metricas,
            "__TIMEZONE__": projeto.youtube.timezone,
            "__FONTE_UID__": config.fonte_uid,
            "__DATASET__": "\n".join(linhas),
            "__ARQUIVO_DATASET__": config.arquivo_dataset,
        }
        modelo = obter_objeto(validar_json(config.modelo))
        resultado = self.substituir_valores(modelo, substituicoes)
        destino = raiz / config.arquivo_saida
        destino.parent.mkdir(parents=True, exist_ok=True)
        temporario = destino.with_suffix(".tmp")
        temporario.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n")
        temporario.replace(destino)
        return destino

    @staticmethod
    def substituir_valores(valor: ValorJson, substituicoes: dict[str, str]) -> ValorJson:
        if isinstance(valor, str):
            for marcador, texto in substituicoes.items():
                valor = valor.replace(marcador, texto)
            return valor
        if isinstance(valor, list):
            return [GeradorDashboard.substituir_valores(item, substituicoes) for item in valor]
        if isinstance(valor, dict):
            resultado: ObjetoJson = {
                chave: GeradorDashboard.substituir_valores(item, substituicoes)
                for chave, item in valor.items()
            }
            return resultado
        return valor


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gerar dashboard Grafana do RAG")
    parser.add_argument("--configuracao", type=Path, required=True)
    parser.add_argument("--raiz", type=Path, required=True)
    argumentos = parser.parse_args()
    print(GeradorDashboard().gerar_arquivo(argumentos.configuracao, argumentos.raiz))
