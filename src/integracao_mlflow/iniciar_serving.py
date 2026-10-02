"""Bootstrap do serviço existente com dependências e opções configuradas."""

import os
import subprocess
import sys
from pathlib import Path


def iniciar_servico() -> None:
    # PyYAML é necessário antes de interpretar o contrato operacional.
    subprocess.run([sys.executable, "-m", "pip", "install", "PyYAML"], check=True)
    import yaml

    raiz = Path(os.environ["RAG_SERVING_RAIZ"])
    configuracao = Path(os.environ["RAG_SERVING_CONFIGURACAO"])
    dados: object = yaml.safe_load(configuracao.read_text())
    if not isinstance(dados, dict):
        raise ValueError("Configuração serving inválida")
    indice = str(dados["indice_torch"])
    pacote = str(dados["pacote_torch"])
    subprocess.run(
        [sys.executable, "-m", "pip", "install", pacote, "--index-url", indice], check=True
    )
    requisitos = raiz / str(dados["arquivo_requisitos"])
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requisitos)], check=True)
    from integracao_mlflow.configuracao_serving import ConfiguracaoServing

    config = ConfiguracaoServing.model_validate(dados)
    model_uri = (raiz / config.arquivo_uri).read_text().strip()
    if not model_uri:
        raise ValueError("Publique o modelo antes de iniciar serving")
    os.execv(
        sys.executable,
        [
            sys.executable,
            "-m",
            "mlflow",
            "models",
            "serve",
            "--model-uri",
            model_uri,
            "--env-manager",
            "local",
            "--host",
            config.host_serving,
            "--port",
            str(config.porta_serving),
            "--workers",
            str(config.workers_serving),
            "--timeout",
            str(config.timeout_serving),
        ],
    )


if __name__ == "__main__":
    iniciar_servico()
