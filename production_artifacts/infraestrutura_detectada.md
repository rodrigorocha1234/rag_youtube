# Infraestrutura detectada

Compose preservado: docker-compose.yml. `docker compose config --quiet` aprovado. Perfis servico_ml, dashboard e serving. Rede existente mlflow-network (172.30.0.0/16).

| Serviço | Endpoint publicado/configurado | Diagnóstico inicial |
|---|---|---|
| postgres/pgvector | localhost:5432 | saudável |
| storage RustFS | localhost:9000/9001 | saudável |
| mlflow | .env MLFLOW_PORT | reiniciando; verificar logs |
| grafana | localhost:3000 | volume sem permissão |
| prometheus | localhost:9090 | volume sem permissão |
| loki | localhost:3100 | em execução |
| alloy | localhost:12345 | em execução |
| metricas-treino | interno :8000 | script montado é diretório |

Serviços auxiliares pgvector-init e create-bucket existentes. mlflow-serving refere-se a aplicação anterior (app_build/configuracoes), não à implementação RAG. Nenhum serviço ou Compose criado. Estado observado registrado em estado_compose.txt, não representa monitoramento contínuo.

## Correções executadas no Compose existente

Comando do MLflow reescrito numa única linha para eliminar continuações inválidas. Proprietários dos volumes Grafana (472) e Prometheus (65534) corrigidos por execuções temporárias dos próprios serviços, removidas ao fim; sudo local exigia senha. Exportador aponta para src/observabilidade_app/exportador_metricas.py e lê production_artifacts/metricas_pipeline.prom. Imagem do exportador atualizada para Python >=3.12 por variável METRICAS_PYTHON_VERSION. Nenhum serviço acrescentado.

PostgreSQL confirmou extensão vector 0.8.7. Integração PGVectorStore criou uma tabela exclusiva temporária, verificou upsert/consulta/filtros/reinicialização e removeu a tabela; resultado 1 passed. MLflow confirmou persistência de trace sintético. Prometheus saudável; exporter Python 3.12.15 com /metrics HTTP 200 reconfirmado após troca de imagem. Grafana deixou o ciclo de reinicialização e está executando migrações SQLite; healthcheck ainda não aprovado no último snapshot. Não considerar Grafana pronto até /api/health responder.
