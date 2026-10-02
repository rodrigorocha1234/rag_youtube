---
name: coletar-youtube
description: Implementa ingestão tipada de canais, vídeos, comentários e respostas via YouTube Data API.
---
Leia configurações de YAML. Carregue `YOUTUBE_API_KEY` de `youtube.env`. Use Adapter para isolar a API externa. Respeite paginação, quota, comentários desabilitados, retries configuráveis e a janela `dias_publicacao_atras`. Salve payload bruto na camada Bronze sem transformação destrutiva.
