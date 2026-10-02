# AGENTS.md — RAG de Comentários do YouTube

## Missão
Construir e manter um RAG de comentários de vídeos/canais do YouTube com Data Lake Bronze/Prata/Ouro, Hugging Face, LangChain, PostgreSQL/pgvector e MLflow GenAI.

## Regras obrigatórias
1. Leia `rules/`, `specs/` e o ExecPlan ativo antes de implementar mudanças relevantes.
2. NÃO crie Docker Compose. Descubra e leia o Compose já ativo antes de integrar infraestrutura.
3. Carregue o segredo `YOUTUBE_API_KEY` a partir de `youtube.env`; nunca registre o valor em logs, traces, MLflow ou arquivos versionados.
4. Proibido hardcoded operacional: parâmetros, modelos, limites, nomes de serviços, portas, caminhos, top-k e flags devem vir de YAML/env.
5. Python >= 3.12; tipagem forte; `Any` é proibido em código próprio.
6. Pacotes e módulos Python próprios devem ter exatamente duas palavras separadas por `_`, salvo nomes técnicos obrigatórios como `__init__.py`, `__main__.py` e `conftest.py`.
7. Uma classe principal por arquivo `.py`, exceto estruturas coesas como dataclasses, TypedDicts, Enums e exceções.
8. Nomes próprios do projeto em português.
9. Prefira composição e padrões GoF quando houver variação real: Strategy, Factory Method, Adapter, Observer, Chain of Responsibility e Command.
10. Não use `if/elif` extensos para selecionar comportamentos quando Strategy/Registry/Factory resolverem melhor.
11. Pandas: proibir `iterrows()`, loops linha a linha, atribuição célula a célula, `apply(axis=1)` evitável e conversões para listas/dicts apenas para processamento linha a linha.
12. Ordem preferencial Pandas: vetorização → `.str/.dt/.cat` → `assign/where/mask` → NumPy vetorizado → `groupby.agg/transform` → `merge/join` → `isin/between` → `fillna/replace/clip`.
13. Não sombreie stdlib ou dependências com nomes de módulos internos.
14. Use `@override` de `typing` em Python 3.12+ quando houver sobrescrita explícita.
15. Use `ABC`/`@abstractmethod` apenas quando herança fizer parte real do design; não use `raise NotImplementedError` permanentemente.
16. Não deixe o código verboso. Classes e métodos devem ter responsabilidade única.
17. Todo fluxo deve produzir logs estruturados, métricas Prometheus e tracing MLflow GenAI quando aplicável.
18. Antes de concluir qualquer tarefa, execute testes, type checking e validações arquiteturais pertinentes.

## Ordem de trabalho
1. Inspecionar ambiente e Compose existente.
2. Atualizar/validar specs e rules.
3. Criar/atualizar ExecPlan em `plans/plano_atual.md`.
4. Implementar por módulo.
5. Executar QA.
6. Produzir artefatos em `production_artifacts/`.

## Agentes lógicos
- Arquiteto: especificação, arquitetura, contratos e ExecPlan.
- Engenheiro de Dados: YouTube API, ingestão e Data Lake.
- Engenheiro RAG: documentos, embeddings, pgvector, retrieval, reranking e geração.
- Engenheiro MLOps/GenAI: MLflow GenAI, tracing, evaluation e observabilidade.
- QA: testes, tipagem, segurança, arquitetura e regressões.
- Operação: valida Compose existente e integrações sem criar infraestrutura duplicada.
