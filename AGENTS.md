# AGENTS.md — Contrato do projeto

Este repositório implementa um RAG de comentários do YouTube orientado a arquitetura multiagente para Codex.

## Regras globais
1. Leia `rules/` antes de alterar código.
2. Leia as `specs/` relacionadas ao módulo alterado.
3. Para mudanças grandes, crie/atualize um ExecPlan em `plans/`, seguindo `.agent/PLANS.md`.
4. Antes de qualquer decisão de infraestrutura, leia o Docker Compose existente com `docker compose config` e `docker compose ps`.
5. Nunca criar outro `docker-compose.yml` ou `compose.yaml`.
6. Nunca persistir dados de runtime localmente. Dados persistentes vão para o S3 compatível definido pelo Compose, pgvector ou MLflow Artifact Store.
7. Segredos nunca entram em YAML/código. `YOUTUBE_API_KEY` vem de `youtube.env`/ambiente.
8. Python mínimo: 3.12. Proibido `Any`. Tipagem strict.
9. Uma classe principal por arquivo `.py`, exceto dataclasses, TypedDict, Enums e exceções coesas.
10. Nomes próprios do projeto em português. Módulos/pacotes Python próprios devem ter exatamente duas palavras, exceto nomes técnicos exigidos pelas ferramentas.
11. Prefira composição e padrões GoF a condicionais arquiteturais espalhadas.
12. Não usar APIs deprecated. Conferir documentação/versão instalada antes de introduzir dependências.
13. Proibido processamento linha a linha em pandas quando houver alternativa vetorizada.
14. Antes do handoff: testes, type checker strict, lint e auditoria arquitetural.
