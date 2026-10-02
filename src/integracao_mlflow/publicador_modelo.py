"""Publica snapshot RAG no MLflow existente sem arquivos de credenciais."""

import argparse
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import mlflow
import yaml
from dotenv import load_dotenv

from configuracao_app.carregador_config import CarregadorConfig
from documentos_rag.documento_rag import DocumentoRag
from integracao_mlflow.configuracao_serving import ConfiguracaoServing
from integracao_mlflow.modelo_consulta import ModeloConsulta


class PublicadorModelo:
    def publicar_modelo(self, configuracao: Path, raiz: Path) -> str:
        config = ConfiguracaoServing.model_validate(yaml.safe_load(configuracao.read_text()))
        projeto = CarregadorConfig.carregar_projeto(raiz / config.arquivo_projeto)
        modelos = CarregadorConfig.carregar_modelos(raiz / config.arquivo_modelos)
        CarregadorConfig.validar_operacao(projeto, modelos)
        load_dotenv(raiz / projeto.projeto.arquivo_ambiente, override=False)
        if not projeto.mlflow.uri_rastreamento:
            raise ValueError("URI MLflow requerida para publicação")
        uri = os.path.expandvars(projeto.mlflow.uri_rastreamento)
        mlflow.set_tracking_uri(uri)
        mlflow.set_experiment(projeto.mlflow.experimento)
        documentos: dict[str, DocumentoRag] = {}
        ouro = raiz / projeto.datalake.diretorio_raiz / projeto.datalake.camada_ouro
        for arquivo in sorted(ouro.glob("*.jsonl")):
            for linha in arquivo.read_text().splitlines():
                if linha.strip():
                    doc = DocumentoRag.model_validate_json(linha)
                    anterior = documentos.get(doc.documento_id)
                    if anterior is None or str(doc.metadados.get("data_atualizacao", "")) >= str(
                        anterior.metadados.get("data_atualizacao", "")
                    ):
                        documentos[doc.documento_id] = doc
        with TemporaryDirectory() as temporario:
            snapshot = Path(temporario) / config.arquivo_snapshot
            snapshot.write_text("\n".join(doc.model_dump_json() for doc in documentos.values()))
            with mlflow.start_run(run_name=config.nome_run):
                info = mlflow.pyfunc.log_model(
                    name=config.nome_modelo,
                    python_model=ModeloConsulta(config),
                    artifacts={
                        config.artefato_projeto: str((raiz / config.arquivo_projeto).resolve()),
                        config.artefato_modelos: str((raiz / config.arquivo_modelos).resolve()),
                        config.artefato_documentos: str(snapshot),
                    },
                    pip_requirements=config.requisitos,
                )
                model_uri = str(info.model_uri)
        requisitos = raiz / config.arquivo_requisitos
        requisitos.parent.mkdir(parents=True, exist_ok=True)
        requisitos.write_text("\n".join(config.requisitos) + "\n")
        recibo = raiz / config.arquivo_recibo
        recibo.parent.mkdir(parents=True, exist_ok=True)
        recibo.write_text(
            json.dumps(
                {
                    "model_uri": model_uri,
                    "documentos": len(documentos),
                    "origem": "snapshot_ouro",
                    "inferencia_real_com_contexto": False,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )
        arquivo_uri = raiz / config.arquivo_uri
        arquivo_uri.parent.mkdir(parents=True, exist_ok=True)
        arquivo_uri.write_text(model_uri + "\n")
        return model_uri


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Publicar modelo RAG para MLflow Serving")
    parser.add_argument("--configuracao", type=Path, required=True)
    parser.add_argument("--raiz", type=Path, required=True)
    argumentos = parser.parse_args()
    print(PublicadorModelo().publicar_modelo(argumentos.configuracao, argumentos.raiz))
