# Relatório final — RAG de comentários YouTube

## Entrega

Implementados configuração tipada, YouTube paginado com quota/retries, janela temporal, canais múltiplos, comentários e respostas, Bronze bruto, Prata vetorizada/deduplicada, Ouro com proveniência, embeddings Hugging Face, PGVectorStore, filtros, estratégias semântica/híbrida, reranking, geração LangChain com fontes, logs estruturados, Prometheus e tracing/evaluation MLflow GenAI. CLI em pipeline_principal e documentação README.md.

Canal autorizado: UCoLf24olVUtKOsSXlqv_-ag. Modelos menores configurados nos YAMLs: MiniLM multilíngue para embeddings, Qwen2.5-0.5B-Instruct para geração e mmarco-mMiniLMv2 para reranking. Dataset sintético v1 em avaliacoes/dataset_rag_v1.jsonl; não representa coleta real.

## Evidências

- Gate local: 87 testes aprovados, 1 integração externa ignorada por padrão.
- Mypy strict: 54 fontes aprovadas.
- Ruff: aprovado.
- Compose existente: validação estrutural aprovada; não foi criado Compose nem serviço adicional.
- PGVectorStore real: 1 teste externo aprovado com embeddings determinísticos e tabela temporária removida; persistência, filtros, upsert e inicialização repetida.
- PostgreSQL: pgvector 0.8.7 presente.
- MLflow remoto: trace sintético persistido e confirmado pelo cliente; verificacao_mlflow.json.
- Exportador Prometheus: HTTP 200 reconfirmado após atualização da imagem; runtime Python 3.12.15.

## Correções do QA

Separação de protocolos, estruturas de configuração coesas reconhecidas pela auditoria, tipagem pandas, limites específicos por recurso da API, detecção de tokens repetidos, retries seguros, validações de YAML, conversão NaN→None na fronteira de serialização, filtros de intervalo, top-k sem reranking e inicialização idempotente do índice. Infra existente reparada: comando MLflow, permissões dos volumes e script/exportador.

## Bloqueios e limites

`youtube.env` não existe. A validação operacional foi executada e falhou de forma segura antes de qualquer coleta. Não foram baixados modelos ou executadas coleta YouTube, inferência/reranking HF e avaliação factual real. A instalação de produção requer o extra `modelos` conforme README. Não afirmar execução completa do canal ou qualidade factual.

A recuperação lexical usa o lote Ouro fornecido à fábrica, enquanto a busca vetorial consulta o índice persistido; deduplicação Prata ocorre por lote. Grafana está em migração e seu healthcheck final deve ser confirmado no snapshot de infraestrutura. Gate local APROVADO; gate ponta a ponta PENDENTE_DE_SEGREDO_E_MODELOS. Sem credenciais reais nos artefatos.
