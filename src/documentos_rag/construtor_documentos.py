"""Conversão da Prata em documentos com proveniência."""

from documentos_rag.documento_rag import DocumentoRag
from dominio_youtube.comentario_youtube import ComentarioYoutube


class ConstrutorDocumentos:
    def construir_documentos(self, registros: list[ComentarioYoutube]) -> list[DocumentoRag]:
        return [
            DocumentoRag(
                documento_id=item.comentario_id,
                conteudo=item.texto_normalizado,
                metadados={
                    "canal_id": item.canal_id,
                    "video_id": item.video_id,
                    "comentario_id": item.comentario_id,
                    "comentario_pai_id": item.comentario_pai_id,
                    "data_publicacao": item.data_publicacao.isoformat(),
                    "data_atualizacao": item.data_atualizacao.isoformat(),
                    "data_ingestao": item.data_ingestao.isoformat(),
                    "quantidade_likes": item.quantidade_likes,
                    "tipo_documento": item.tipo_documento,
                    "fonte": f"https://www.youtube.com/watch?v={item.video_id}&lc={item.comentario_id}",
                },
            )
            for item in registros
        ]
