---
name: construir-lake
description: Implementa as camadas Bronze, Prata e Ouro do Data Lake com contratos tipados e processamento vetorizado.
---
Bronze preserva payload bruto. Prata normaliza, tipa, limpa e deduplica. Ouro produz documentos prontos para RAG com metadados e proveniência. Pandas deve ser vetorizado; não use `iterrows()` ou loops linha a linha quando houver alternativa vetorial.
