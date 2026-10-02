# YouTube Comments RAG — Codex Multiagent

Projeto-base para RAG de comentários do YouTube por **canal**, **vídeo** e **canal + vídeo**.

## Stack
- Python 3.12+
- YouTube Data API v3
- LangChain
- Hugging Face
- PostgreSQL + pgvector
- MLflow GenAI / Agent Server
- S3 compatível do Docker Compose existente
- Prometheus / Grafana / Loki / Alloy quando disponíveis

## Importante
Este projeto **não inclui Docker Compose**. Antes de implementar conexões, execute:

```bash
docker compose config
docker compose ps
```

Mapeie os serviços reais para as variáveis de ambiente/YAML sem hardcode.

## Segredo YouTube
Crie `youtube.env` a partir de `youtube.env.exemplo` e defina `YOUTUBE_API_KEY`.

## Fluxo de dados
YouTube → Bronze S3 → Prata S3 → Ouro S3 → Hugging Face embeddings → pgvector → LangChain retrieval → LLM → MLflow tracing/evaluation/serving.

## Fluxo de engenharia
AGENTS.md → rules → specs → ExecPlan → agentes especializados → testes → auditoria.
