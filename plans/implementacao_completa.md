# Implementação completa

## Objetivo e contexto
Implementar as specs atuais em Python 3.12, preservando alterações prévias. O contrato de ExecPlan removido foi lido via git show HEAD:.agent/PLANS.md. Persistência de negócio apenas S3, pgvector e MLflow.

## Infraestrutura detectada
Compose único existente. PostgreSQL pg15/pgvector :5432, RustFS :9000, MLflow :5000, Grafana :3000, Loki :3100, Alloy :12345, Prometheus :9090; rede mlflow-network 172.30.0.0/16. Exportador reiniciando; serving referencia módulos removidos. Não criar Compose nem recriar volumes.

## Contratos e decisões
Configuração YAML validada; segredos carregados do ambiente/youtube.env. Bronze preserva páginas; Prata normaliza comentários e respostas; Ouro cria documentos determinísticos com hash. Adapters YouTube/S3/HF/MLflow. PGVectorStore com colunas explícitas de filtro; estratégias canal/vídeo/ambos e cadeia de pós-processamento. Observabilidade sem labels de IDs. CLI para ingestão, indexação, consulta, avaliação e Agent Server.

## Sequência e módulos
1. Infraestrutura e contratos (specs visão/arquitetura/contratos_api).
2. Configuração, cliente_youtube, descoberta_videos, ingestao_comentarios (spec ingestao_youtube).
3. armazenamento_s3 e processamento_bronze/prata/ouro (contratos lake).
4. modelo_embeddings, armazenamento_vetorial, recuperacao_contexto, pipeline_rag e geracao_respostas (modelo_vetorial/recuperacao_rag).
5. rastreamento_mlflow, avaliacao_genai, metricas_sistema, aplicação e serving (servico_mlflow/observabilidade).
6. Testes, auditoria e documentação (estrategia_testes).

## Dependências e riscos
Verificar APIs instaladas/documentação primária antes de implementar. Downloads HF e API YouTube dependem de rede/credenciais; separar testes determinísticos de integração real. Não executar coleta paga sem configuração válida. Concorrência incremental e falhas parciais exigem hashes e commit após indexação. Model caches são recursos técnicos; dados de negócio não usam filesystem.

## Critérios de aceite e testes
Paginação, retry, quota, commentsDisabled, respostas completas, normalização, deduplicação, idempotência, filtros de escopo, embeddings/reranking, tracing/evaluation/serving, métricas e proteção de segredos. pytest, mypy strict, ruff lint/format, auditoria de dependências e arquitetura. Integrações indisponíveis devem ser registradas como não verificadas.

## Checkpoints
- [x] Leitura dos contratos e inspeção Compose.
- [ ] Ingestão e lake.
- [ ] Indexação e consulta.
- [ ] MLflow, serving e observabilidade.
- [ ] Quality gates e entrega.

## Rollback
Mudanças de código revisáveis via git diff; não reverter trabalho prévio. Não apagar buckets/tabelas/volumes. Registrar handoffs, resultados e pendências neste plano.
