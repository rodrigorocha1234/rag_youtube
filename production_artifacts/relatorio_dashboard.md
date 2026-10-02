# Correção do dashboard RAG no Grafana

Diagnóstico confirmado: Grafana saudável e provider ativo, mas somente dashboard imobiliário disponível. dataset_rag_v1.jsonl contém exemplos de avaliação e não é uma definição de dashboard. metricas_pipeline.prom ausente.

Criado dashboard RAG de Comentários do YouTube, UID rag-comentarios-youtube, com 11 painéis e prévia sintética do dataset. Modelo e parâmetros em configuracao/dashboard_rag.yaml; gerador tipado em observabilidade_app/gerador_dashboard.py. JSON salvo no diretório já provisionado. Nenhum Compose ou serviço novo; dashboards legados preservados.

Verificação operacional: dashboard obtido pela API Grafana com arquivo de provisionamento dashboard_comentarios.json, fonte Prometheus status OK, exportador ml_service up=1. Nove consultas PromQL executadas contra Prometheus e aprovadas. Séries de métricas RAG ausentes, exibidas como Sem dados; não publicados scores ou métricas artificiais. Evidência detalhada em verificacao_dashboard.json. A API desta versão devolve provisioned=false apesar de apontar o arquivo carregado pelo provider; esse comportamento foi registrado sem ocultar o resultado.

Grafana registra também erro em um JSON legado com conteúdo null (previsao-imobiliaria.json); o dashboard RAG foi carregado e confirmado independentemente desse arquivo, preservado nesta correção.

QA: 91 testes aprovados/1 integração externa ignorada; mypy strict 56 fontes aprovado; Ruff aprovado. Tests de contrato cobrem relação entre séries reais do monitor e consultas, namespace configurável, dataset sintético, preservação do destino em caso de dataset inválido e ausência de taxas/fallback zero artificiais. Todos os serviços observados com healthcheck definido estavam saudáveis.

Acesso: http://localhost:3000/d/rag-comentarios-youtube/rag-de-comentarios-do-youtube
