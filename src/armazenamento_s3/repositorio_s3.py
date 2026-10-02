import json

from mypy_boto3_s3.client import S3Client
from pydantic import JsonValue

from dominio_youtube.contratos_ingestao import ADAPTADOR_JSON


class RepositorioS3:
    def __init__(self, cliente: S3Client, bucket: str) -> None:
        self.cliente = cliente
        self.bucket = bucket

    def salvar_json(self, chave: str, valor: JsonValue) -> None:
        conteudo = json.dumps(valor, ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.cliente.put_object(
            Bucket=self.bucket, Key=chave, Body=conteudo, ContentType="application/json",
        )

    def ler_json(self, chave: str) -> JsonValue:
        resposta = self.cliente.get_object(Bucket=self.bucket, Key=chave)
        corpo = resposta["Body"]
        try:
            return ADAPTADOR_JSON.validate_json(corpo.read())
        finally:
            corpo.close()

    def listar(self, prefixo: str) -> list[str]:
        paginador = self.cliente.get_paginator("list_objects_v2")
        return [
            item["Key"] for pagina in paginador.paginate(Bucket=self.bucket, Prefix=prefixo)
            for item in pagina.get("Contents", []) if "Key" in item
        ]
