# ExecPlan — RAG de comentários YouTube

## Objetivo e contexto
Implementar o scaffold conforme rules/ e specs/, preservando o Compose existente. Python >=3.12, tipagem strict sem Any, módulos em português com duas palavras, configuração operacional YAML/env e segredo exclusivamente youtube.env.

## Decisões e contratos
Configuração Pydantic extra=forbid. Adaptadores isolam YouTube, Hugging Face, PGVectorStore e MLflow. Bronze guarda payload bruto; Prata normaliza/deduplica; Ouro contém documentos com proveniência. Retrieval usa registro de estratégias semântica/híbrida. Testes usam doubles; execução externa só com configuração válida. Configuração incompleta falha sem expor segredos.

## Módulos afetados
src/configuracao_app, coleta_youtube, armazenamento_lake, dominio_youtube, documentos_rag, embeddings_texto, armazenamento_vetor, recuperacao_rag, geracao_resposta, observabilidade_app, integracao_mlflow, avaliacao_rag, pipeline_principal; tests/, configuracao/, pyproject.toml, README.md, production_artifacts/.

## Etapas e status
- [x] Arquiteto: ler instruções, specs, rules e revisar plano.
- [x] Operação: validar Compose existente e inventariar ambiente.
- [x] Configuração: validar YAML/env sem imprimir valores secretos.
- [x] Dados: paginação, janela temporal, quota/retries, comentários/respostas, Bronze/Prata/Ouro.
- [x] RAG: embeddings, PGVectorStore, filtros, estratégias, reranking e geração com fontes.
- [x] MLOps: logs JSON, Prometheus, MLflow GenAI e avaliação.
- [x] QA: pytest, mypy strict, lint e arquitetura; corrigir e repetir.
- [x] Relatórios finais.

## Riscos e mitigação
API/rede/modelos/serviços podem estar indisponíveis; registrar bloqueios reais separadamente de testes isolados. Não inventar canais, credenciais ou modelo de geração. Não alterar/duplicar infraestrutura. Evitar coleta e downloads enquanto configuração é placeholder.

## Testes e aceite
Unitário/contrato: paginação, quota, janela, deduplicação, proveniência, filtros, recuperação, ausência de contexto, métricas/tracing e validação estrita. Integrações externas opt-in e explicitamente relatadas. Gate local exige pytest, mypy strict, lint e auditoria arquitetural aprovados; gate operacional exige configurações completas e serviços verificados.

## Rollback
Remover somente arquivos produzidos pela implementação; preservar arquivos de configuração locais, credenciais, volumes e Compose.

## Resultado e pendências operacionais
Gate local APROVADO: pytest 87 passed/1 skipped, mypy strict 54 fontes, Ruff e Compose aprovados. PGVectorStore externo 1 passed; MLflow remoto span sintético persistido. Infra existente reparada sem adicionar serviços; detalhes em production_artifacts/infraestrutura_detectada.md.

Gate ponta a ponta PENDENTE: youtube.env ausente, modelos HF não baixados/inferência não executada, avaliação factual depende de dataset real/scorers. Usuário autorizou canal UCoLf24olVUtKOsSXlqv_-ag e modelos menores, já configurados. Grafana migra SQLite; healthcheck final separado no snapshot. Após criar youtube.env, instalar extra modelos, validar CLI e executar comando README; registrar nova evidência operacional antes de fechar o gate ponta a ponta.

## Documentação de uso
- [x] Criado docs/guia_uso.md com instalação, configurações, CLI, resultados, observabilidade, QA e troubleshooting, conferido contra a implementação; README atualizado com link. Sem alteração de código ou infraestrutura.

## Correção do dashboard Grafana
Objetivo: disponibilizar dashboard do RAG no Grafana existente e explicar a relação com dataset_rag_v1.jsonl. Diagnóstico: provider funcional, apenas painéis imobiliários presentes, sem arquivo metricas_pipeline.prom.

Decisões/contratos: acrescentar dashboard JSON ao diretório já montado, com fonte Prometheus provisionada, namespace/target selecionáveis, snapshot por execução e exemplos sintéticos do dataset identificados. Não produzir scores fictícios. Sem novo Compose ou serviço. Configurações de dashboard em YAML; geração de JSON via módulo tipado para suportar namespace/caminhos configuráveis.

Arquivos: configuracao/dashboard_rag.yaml, src/observabilidade_app/configuracao_dashboard.py e gerador_dashboard.py, config_ob/dashboards/dashboard_comentarios.json, docs/guia_uso.md, specs/observabilidade_rag.md, tests/testes_integracao/teste_dashboard.py, production_artifacts/verificacao_dashboard.json.
Riscos: um arquivo JSON legado contém null e gera erro de título vazio; preservar legados e atribuir UID único ao RAG. Snapshot reinicia contagens por execução, logo queries não devem interpretar contadores como taxas contínuas. Falta de execução não deve aparecer como zero factual.
Testes/aceite: JSON válido e UID único RAG, expressões compatíveis com métricas reais, snapshot declarado, dataset sintético identificado, pytest/mypy/ruff; confirmar dashboard provisionado e datasource/target via APIs reais.
Rollback: remover apenas novo JSON/YAML/gerador; dashboards anteriores e volumes preservados.
- [x] Diagnóstico e plano.
- [x] Gerar dashboard configurado e documentação.
- [x] QA e confirmação API Grafana/Prometheus: 91 testes/1 skipped, mypy56, Ruff; dashboard disponível, datasource OK, 9 consultas válidas, exportador up=1. Séries RAG ainda ausentes, sem dados artificiais.

## Exemplos de resultado
- [x] Incluídos exemplos fictícios com fontes e sem contexto no guia, JSONs em production_artifacts e prévia textual no dashboard RAG. Contratos JSON validados; sem publicação de métricas artificiais.

## MLflow Model Serving /invocations
Objetivo autorizado: gerar respostas via /invocations, reutilizando mlflow-serving existente. Sem coleta por requisição; modelo pyfunc recebe lista de perguntas/filtros e devolve respostas/fontes. Artefatos do modelo contêm YAMLs e documentos Ouro, nunca youtube.env/.env. Configuração de serving em YAML/env. Snapshot vazio retorna evidência insuficiente sem carregar HF; documentos disponíveis habilitam retrieval/reranking/geração.

Arquivos: integracao_mlflow/modelo_consulta.py, publicador_modelo.py, configuracao/servico_rag.yaml; factory RAG separa indexação de consulta; docker-compose.yml serviço mlflow-serving existente, docs e testes de contrato. Reusar API MLflow de publicação e serving oficial.
Riscos: pesos ausentes, ouro vazio, dependências pesadas, ambiente contêiner distinto do host. Configuração de conexão/tracking será resolvida no ambiente de serving; nenhum segredo serializado. Sobrescrita do serviço inativo legado para RAG, sem duplicar infraestrutura. Artefatos carregados pelo endpoint são snapshot da publicação; republicar após ingestão.
Testes/aceite: assinatura pyfunc, filtros e lote, não chamar coleta/indexação na inferência, sanitização, resposta vazia, pytest/mypy/ruff e POST real /invocations. Rollback: restaurar configuração anterior do serviço preservando todos os volumes.
- [x] Inspecionar Compose/contratos e esclarecer usuário: gerar via /invocations.
- [x] Implementar e publicar modelo.
- [x] Reutilizar serviço e confirmar invocations real: HTTP 200, snapshot vazio, trace OK e métrica real no Prometheus.
- [x] QA e documentação: 99 testes/1 skipped, mypy60, Ruff, Compose; guia seção12 e relatorio_serving.md.

## Correção ValueError de configuração YouTube
Diagnóstico: youtube.env ausente; chave operacional disponível em .env. Copiar somente YOUTUBE_API_KEY para arquivo local configurado (permissão 0600), preservando .env e sem registrar valor. Melhorar CLI com erro controlado/código/orientação para arquivo ausente/chave inválida; manter mensagens de fornecedores ocultas. Arquivos: carregador_config, erro_configuracao, CLI, testes e docs. Validar --validar, regressões/segurança/mypy/arquitetura. Rollback: reverter alterações de diagnóstico; arquivo local não versionado contém apenas chave já existente.
- [x] Corrigir arquivo local (0600) e validar configuração: --validar retorna configuracao_valida.
- [x] Diagnóstico seguro, QA e relatório: erros controlados para arquivo ausente/chave inválida; valores de fornecedores ocultos. Chave local resolvida; autenticação API e inferência continuam sem nova validação ponta a ponta nesta correção.
