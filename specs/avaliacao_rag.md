# Avaliação RAG
Manter dataset versionado de avaliação com pergunta, resposta esperada e evidências relevantes. Avaliar retrieval, geração e RAG completo com MLflow GenAI.

Dataset inicial versionado pelo nome `avaliacoes/dataset_rag_v1.jsonl`, com dados sintéticos explicitamente identificados. Ele testa o contrato de evidências e recusa sem contexto e não representa comentários reais nem benchmark de produção. Para avaliação de produção, criar próxima versão com amostras do canal e evidências revisadas. `AvaliadorGenai` recebe scorers explicitamente configurados por escopo; executar e registrar resultados reais antes de alegar groundedness/relevance/correctness.
