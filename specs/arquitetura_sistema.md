# Arquitetura do Sistema
Fluxo: YouTube API → Bronze → Prata → Ouro → Embeddings Hugging Face → PostgreSQL/pgvector → Retrieval/Reranking → LangChain → LLM Hugging Face → Resposta + Fontes → MLflow GenAI/Prometheus.

## Implementação e fronteiras
Configuração validada por Pydantic (extra=forbid) em configuracao_app. Adaptadores para YouTube, Hugging Face, PGVectorStore e MLflow; orquestração em pipeline_principal. Cada página da API é persistida antes da transformação. Prata limpa e deduplica de forma vetorizada; Ouro mantém fontes por comentário.

O lake usa JSONL atômico por lote. Deduplicação Prata ocorre por lote; indexação usa UUID estável e upsert. O retriever híbrido funde rankings com RRF configurado. Filtros aceitam igualdade e intervalos de publicação. A busca lexical usa o lote Ouro fornecido; a semântica consulta o índice persistente. Qualidade factual é medida pelos scorers GenAI, não pelo simples retorno de fontes.

Gate local não equivale a execução YouTube/modelos real. Integrações opt-in possuem evidência separada nos relatórios. Nenhum Compose ou serviço adicional é criado.
