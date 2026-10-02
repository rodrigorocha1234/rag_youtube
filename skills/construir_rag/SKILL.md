---
name: construir-rag
description: Implementa o RAG com Hugging Face, LangChain e PostgreSQL/pgvector.
---
Use LangChain como camada de composição, não como domínio. Embeddings e geração devem vir de configuração YAML. Use `langchain-postgres`/`PGVectorStore`. Aplique Strategy para retrieval e modelos, Factory/Registry para seleção por configuração e Adapter para integrações externas. Preserve canal_id, video_id, comentario_id e demais metadados de proveniência.
