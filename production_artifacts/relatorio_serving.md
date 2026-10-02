# MLflow Model Serving — resultados RAG via /invocations

Implementado e ativado o endpoint POST http://localhost:8080/invocations no serviço mlflow-serving já existente. Servidor oficial MLflow pyfunc, Python 3.12, dependências Hugging Face e PyTorch CPU instaladas. Nenhum serviço ou Compose novo.

Publicação captura YAMLs e documentos Ouro; arquivos .env/youtube.env não são artefatos. Serving usa variáveis do contêiner para tracking e PostgreSQL. Requisições não executam coleta ou indexação; factory explicitamente consulta o índice existente. Entrada inputs é lista de objetos com pergunta e filtros textuais opcionais canal_id/video_id; saída predictions contém resposta/fontes.

## Evidências reais
- Modelo: models:/m-574ff4123ea54a758fac87038985f0dd.
- /health HTTP 200, POST /invocations HTTP 200.
- Resposta real salva em resposta_invocations.json; snapshot Ouro vazio retorna evidência insuficiente e fontes vazias. Não houve geração HF com contexto ou coleta de comentários nesta validação.
- Trace tr-cc4d155dceee57745b28d896c16122ab confirmado no MLflow, estado OK.
- Métrica respostas_servidas=1 confirmada no Prometheus e no exportador existente; namespace de serving separado, sem métricas simuladas.
- Dashboard contém painel Respostas pela API MLflow /invocations, confirmado pela API Grafana.
- Todos os serviços com healthcheck estavam saudáveis no snapshot estado_serving.txt.

## QA
99 testes aprovados, 1 integração externa ignorada; mypy strict em 60 fontes aprovado; Ruff e validação Compose aprovados. Testes de serving cobrem lote, filtros, sanitização, pergunta inválida, retorno sem contexto sem HF e factory sem escrita no índice. Evidências em testes_serving.txt, tipagem_serving.txt, lint_serving.txt e verificacao_serving.json.

## Operação
Ingerir/indexar pelo pipeline, publicar com integracao_mlflow.publicador_modelo e reiniciar mlflow-serving após cada republicação. Ver seção 12 de docs/guia_uso.md. O modelo usa snapshot de documentos, não refaz a ingestão durante perguntas. Serving preserva as métricas de ingestão ao exportar em arquivo/namespace separados. Removido scrape legado que consultava /metrics no serviço de inferência (rota inexistente no MLflow oficial); ambas as famílias são coletadas pelo exportador já existente.

## Limites
Inferência HF com documentos e grounding factual continuam sem evidência de execução. SDK infere a assinatura de entrada dos type hints; schema de saída dinâmico é aceito pelo SDK, enquanto objetos retornados seguem contrato próprio resposta/fontes. Código próprio usa tipagem strict sem tipo Any.
