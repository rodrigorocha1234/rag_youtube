# Relatório QA

## Gate final local

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/pytest -q`: **87 aprovados e 1 ignorado**; teste externo pgvector requer ativação explícita.
- `.venv/bin/mypy src --strict`: **aprovado, 54 arquivos próprios**.
- `.venv/bin/ruff check src tests`: **aprovado**.

A suíte cobre configuração, paginação, retries, quota, janela temporal, respostas, Data Lake, deduplicação, documentos, filtros, busca híbrida, proveniência, ausência de contexto, avaliação determinística, métricas, sanitização e arquitetura. Não equivale a execução completa com modelos reais.

## Integrações verificadas

- SDK MLflow com SQLite temporário: criação de span e flush assíncrono aprovados.
- Servidor MLflow existente: span sintético criado pelo `TracadorMlflow`, URI expandida do YAML com `.env`; `flush_trace_async_logging()` e `MlflowClient.get_trace()` confirmaram persistência. Trace `tr-96fdcd7ebda48ca2c3e3cfe9a85b52b7`, estado **OK**. Evidência: `production_artifacts/verificacao_mlflow.json`. Nenhum segredo ou comentário YouTube enviado.
- pgvector: agente principal informa teste explícito aprovado contra banco existente, usando tabela temporária posteriormente removida e embeddings de teste; não comprova embeddings Hugging Face. O gate padrão mantém esse teste externo ignorado.
- Agente principal informa reparos e validação operacional dos serviços existentes MLflow/Grafana/Prometheus e exportador; não foi criado serviço Compose adicional.

## Segurança e avaliação

Logs/traces sanitizam campos sensíveis e segredos conhecidos. Dataset de avaliação é sanitizado recursivamente. Erros dos fornecedores são propagados após fechar o span; apenas o tipo da exceção é enviado ao MLflow, com estado ERROR. Testes verificam essa fronteira.

Fontes correspondem aos documentos finais após recuperação/reranking. Geração sem contexto não chama modelo. Métricas determinísticas de retrieval e correspondência textual não comprovam groundedness factual. Avaliação GenAI requer scorers explícitos nos escopos retrieval, geração e completo; não foi executado juiz externo.

## Limitações materiais

Coleta YouTube, downloads de modelos, geração real Hugging Face, reranking real e avaliação factual externa não foram executados nesta auditoria. O exportador mantém a imagem Python 3.11 herdada do Compose e usa compatibilidade para `typing.override`; a aplicação e o gate de tipagem exigem Python 3.12+. Atualizar a imagem operacional continua necessário para uniformizar o requisito de runtime, sem invalidar a execução verificada do exportador.

O primeiro smoke MLflow em sandbox foi bloqueado pela restrição de sockets; a repetição com escalada autorizada passou. Isso não era indisponibilidade do serviço.
