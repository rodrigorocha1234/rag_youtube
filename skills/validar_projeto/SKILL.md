---
name: validar-projeto
description: Executa o gate final de qualidade antes de considerar uma alteração concluída.
---
Execute pytest, type checker strict, lint, testes de arquitetura, segurança, integração, retrieval e MLflow. Gere `production_artifacts/relatorio_qa.md` com evidências e falhas. Não marque concluído se testes críticos falharem.
