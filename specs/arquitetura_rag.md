# Spec: arquitetura_rag

Separar pipeline de conhecimento (YouTube→S3→embeddings→pgvector) da pipeline de consulta (pergunta→retrieval→reranking→LLM→MLflow).

## Critérios de aceite
- Sem hardcode.
- Sem persistência local.
- Tipagem strict.
- Testes associados.
