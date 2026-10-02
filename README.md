# RAG de comentários do YouTube

Consulte o [guia de uso completo](docs/guia_uso.md) para configuração, execução e solução de problemas.

Pipeline tipado em Python >=3.12: YouTube → Bronze/Prata/Ouro → embeddings Hugging Face → PGVectorStore → recuperação semântica/híbrida → reranking → geração LangChain com fontes. Logs JSON, métricas Prometheus e traces/avaliação MLflow GenAI.

## Instalação

```bash
uv venv --python 3.12
uv pip install --python .venv/bin/python -e '.[qa,modelos]'
```

Os modelos são carregados somente na execução real. A instalação `modelos` inclui PyTorch e Transformers; selecione a distribuição de PyTorch adequada ao hardware. Não é necessário baixar modelos para o gate local.

## Configuração e execução

`configuracao/projeto_rag.yaml` define o canal, janela temporal, quota, retries, lake, retrieval, banco e observabilidade. `configuracao/modelos_rag.yaml` define os modelos, dimensão dos embeddings, prompts e geração. Chaves desconhecidas e configurações inconsistentes falham na validação. O canal informado é `UCoLf24olVUtKOsSXlqv_-ag`; a janela atual seleciona o dia exato de dois dias atrás em America/Sao_Paulo.

Crie `youtube.env` a partir de `youtube.env.example` e preencha a chave localmente. Nunca envie o valor pelo chat ou versionamento. `.env` contém as variáveis da infraestrutura já existente. A conexão PostgreSQL pode ser fornecida pelo nome configurado em `vetor.conexao_ambiente`, ou composta a partir das variáveis configuradas de usuário, senha, banco e porta. A URI MLflow expande variáveis de `.env`.

```bash
PYTHONPATH=src .venv/bin/python -m pipeline_principal \
  --projeto configuracao/projeto_rag.yaml \
  --modelos configuracao/modelos_rag.yaml --raiz . --validar

PYTHONPATH=src .venv/bin/python -m pipeline_principal \
  --projeto configuracao/projeto_rag.yaml \
  --modelos configuracao/modelos_rag.yaml --raiz . \
  --pergunta 'Quais são as principais dúvidas nos comentários?' \
  --canal UCoLf24olVUtKOsSXlqv_-ag
```

Sem `--pergunta`, o fluxo coleta, prepara as camadas e indexa os documentos. Sem documentos na janela, não carrega modelos e devolve a mensagem configurada de evidência insuficiente. A busca lexical considera os documentos da coleta atual; a busca vetorial considera o índice persistido. Para um índice completo, carregue os documentos Ouro correspondentes antes de construir a estratégia híbrida.

O Compose existente foi reutilizado. Nenhum serviço foi adicionado. O exportador `metricas-treino` lê `production_artifacts/metricas_pipeline.prom`, escrito atomicamente pelo pipeline, e o Prometheus já consulta esse serviço. MLflow usa o servidor existente. O exportador usa a imagem Python 3.12 configurada em METRICAS_PYTHON_VERSION; a aplicação e o gate também usam Python 3.12.

## QA

```bash
.venv/bin/pytest -q
.venv/bin/mypy src
.venv/bin/ruff check src tests
docker compose config --quiet
```

O teste PostgreSQL é opt-in. Ele usa embeddings determinísticos para verificar persistência, inicialização repetida e filtros via PGVectorStore; não valida qualidade dos modelos. A tabela deve ser exclusiva para o teste e é removida ao terminar.

```bash
RAG_TESTE_PROJETO=configuracao/projeto_rag.yaml \
RAG_TESTE_MODELOS=configuracao/modelos_rag.yaml \
RAG_TESTE_RAIZ=. RAG_TESTE_TABELA=validacao_rag_contrato \
.venv/bin/pytest -q tests/testes_integracao/teste_pgvector.py
```

`AvaliadorGenai.avaliar_dataset` exige dataset com evidências e scorers explícitos nos escopos retrieval, geração e completo. As métricas locais verificam recuperação e proveniência; factualidade das respostas exige avaliação com os modelos/scorers reais. Relatórios e evidências estão em `production_artifacts/`. Consulte `plans/plano_atual.md` para status e bloqueios operacionais.

## API MLflow Serving

Publique o snapshot com `python -m integracao_mlflow.publicador_modelo --configuracao configuracao/servico_rag.yaml --raiz .` (use PYTHONPATH=src e .venv/bin/python). O serviço existente mlflow-serving recebe perguntas via POST /invocations em formato `inputs`. Consulte a seção 12 do [guia de uso](docs/guia_uso.md) para publicação, inicialização, filtros e exemplo curl. Ouro vazio retorna evidência insuficiente.
