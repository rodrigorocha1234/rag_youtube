# Observabilidade
Métricas: YouTube requests/quota, registros Bronze/Prata/Ouro, embedding throughput/failures, pgvector query latency, retrieval latency/hit-rate/MRR/nDCG, geração latency/tokens/errors, groundedness/relevance/correctness.

## Dashboard provisionado
Dashboard RAG de Comentários do YouTube gerado a partir de configuracao/dashboard_rag.yaml e provisionado pelo provider existente. Consulta snapshot Prometheus por execução (contagens absolutas e histogramas cumulativos do snapshot, sem rate de contadores reiniciados). Exibe disponibilidade do exportador separada da presença de métricas RAG. Dados ausentes não equivalem a zero. O dataset JSONL sintético é exibido como referência textual; qualidade só aparece quando métricas medidas são publicadas. Não existe importação automática de JSONL como dashboard.

Serving publica métricas em namespace/arquivo separados conforme servico_rag.yaml. O exportador existente reúne ingestão e serving em /metrics, consultado pelo target ml_service. O MLflow Model Serving oficial não oferece /metrics nesta configuração; o alvo legado foi retirado. O dashboard tem painel real de respostas_servidas.
