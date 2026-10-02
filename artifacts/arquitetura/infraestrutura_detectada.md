# Infraestrutura detectada

Inspeção: docker compose config (JSON filtrado para não expor credenciais) e docker compose ps.

| Serviço | Endpoint host | Estado |
|---|---|---|
| PostgreSQL pg15 + pgvector | localhost:5432 | healthy |
| RustFS S3 / console | localhost:9000 / 9001 | healthy |
| MLflow | localhost:5000 | healthy |
| Grafana | localhost:3000 | healthy |
| Prometheus | localhost:9090 | healthy |
| Loki | localhost:3100 | ativo, sem healthcheck |
| Alloy | localhost:12345 | ativo, sem healthcheck |
| Exportador metricas-treino | rede interna :8000 | reiniciando; script removido |
| MLflow serving | :8080 previsto | inativo; configuração/módulos removidos |

Rede bridge mlflow-network, subnet 172.30.0.0/16. Perfis servico_ml/dashboard/serving. Healthchecks PostgreSQL pg_isready, RustFS /health, MLflow /health, Grafana /api/health e Prometheus /-/healthy. Credenciais via POSTGRES_*, AWS_*, S3_BUCKET, MLFLOW_*; valores não registrados. Compose mantém volumes locais da infraestrutura; a aplicação não persistirá dados nesses caminhos. Serving antigo precisa ser atualizado no Compose existente. Inicializadores pgvector-init e create-bucket são serviços de execução única. Nenhum container ou volume alterado durante inspeção.
