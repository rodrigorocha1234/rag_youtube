from dominio_youtube.modelos_dominio import ConsultaRag


class PipelineComentariosRag:
    def executar_ingestao(self) -> None:
        raise RuntimeError("Implementar conforme specs e infraestrutura detectada no Docker Compose ativo.")

    def atualizar_indice(self) -> None:
        raise RuntimeError("Implementar conforme specs e infraestrutura detectada no Docker Compose ativo.")

    def consultar_rag(self, consulta: ConsultaRag) -> str:
        raise RuntimeError(f"Pipeline RAG ainda não implementada para: {consulta.escopo}")

    def avaliar_rag(self) -> None:
        raise RuntimeError("Implementar integração MLflow GenAI conforme spec.")
