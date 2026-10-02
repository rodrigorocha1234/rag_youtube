# Pipeline RAG
Consulta → filtros → retrieval → fusão/hybrid search → reranking opcional → top-k → prompt → geração → fontes → tracing/evaluation.

Serving: MLflow pyfunc via /invocations aceita inputs como lista de objetos textuais com pergunta, canal_id/video_id opcionais. Usa snapshot Ouro e índice existente, sem ingestão/indexação na inferência. Devolve predictions com resposta/fontes. Snapshot vazio retorna mensagem configurada sem carregar modelos; republique após preparar os documentos. Modelo publicado não inclui arquivos de segredo.
