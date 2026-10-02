# Guia de uso — RAG de comentários do YouTube

Este guia explica como coletar comentários, preparar o Data Lake e fazer perguntas com fontes. Execute os comandos na raiz do projeto, em um terminal Bash. A aplicação roda no ambiente Python local e se conecta aos serviços do Compose existente.

## 1. Preparar o ambiente Python

Requisitos: Python 3.12 ou superior, `uv`, Docker com Compose e acesso à internet para a API YouTube e o primeiro download dos modelos.

Se ainda não houver ambiente virtual:

```bash
uv venv --python 3.12
```

Instale as dependências de execução, modelos e validação:

```bash
uv pip install --python .venv/bin/python -e '.[qa,modelos]'
.venv/bin/python --version
```

O extra `modelos` instala as bibliotecas de inferência; os pesos são carregados durante a execução. A configuração atual usa CPU. A primeira execução com documentos pode demorar devido ao download e ao carregamento dos modelos.

## 2. Configurar a chave YouTube

Habilite a YouTube Data API v3 no seu projeto Google Cloud e obtenha uma chave autorizada a acessar essa API.

Crie o arquivo local somente se ele ainda não existir:

```bash
if [ ! -f youtube.env ]; then
  cp youtube.env.example youtube.env
fi
```

Abra `youtube.env` no editor e substitua o placeholder pelo valor da chave em `YOUTUBE_API_KEY`. A aplicação lê esse segredo do arquivo indicado em `youtube.arquivo_ambiente`; definir a chave somente no ambiente do terminal não substitui esse arquivo.

Mantenha `.env` e `youtube.env` fora do versionamento. Não inclua seus valores em relatórios ou comandos compartilhados.

## 3. Conferir a infraestrutura existente

O projeto utiliza `docker-compose.yml`. Valide-o sem imprimir a configuração expandida, que pode conter segredos:

```bash
docker compose config --quiet
docker compose config --services
docker compose ps
```

Para iniciar os serviços já definidos de banco, MLflow e armazenamento, junto à observabilidade:

```bash
docker compose --profile servico_ml --profile dashboard up -d
docker compose ps
```

O perfil `serving` atende o RAG via `/invocations`; ele é opcional para o uso da CLI e está descrito na seção 12.

Confira as variáveis já usadas em `.env`, sem alterar suas credenciais:

| Finalidade | Variáveis usadas pela aplicação na configuração atual |
|---|---|
| PostgreSQL | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `PGPORT` |
| Conexão completa opcional | `POSTGRES_CONNECTION_STRING` |
| Porta MLflow | `MLFLOW_PORT` |

O Compose também exige suas próprias variáveis de MLflow, armazenamento e demais serviços. Preserve os valores existentes. A aplicação compõe a conexão PostgreSQL a partir das variáveis acima quando uma conexão completa não estiver definida. O nome de cada variável e o host são configuráveis no bloco `vetor` do YAML.

A aplicação carrega `.env` sem sobrescrever variáveis já exportadas no terminal. Se uma conexão antiga continuar sendo usada, confira essa precedência.

## 4. Ajustar os YAMLs

### Projeto e coleta

Edite [projeto_rag.yaml](../configuracao/projeto_rag.yaml).

| Campo | Uso |
|---|---|
| `youtube.ids_canais` | Lista de canais a coletar |
| `youtube.dias_publicacao_atras` | Distância em dias da data de publicação dos vídeos |
| `youtube.modo_janela_publicacao` | `dia_exato` ou `acumulada` |
| `youtube.timezone` | Fuso usado para comparar as datas |
| `youtube.incluir_respostas` | Coleta também respostas aos comentários |
| `youtube.quota_maxima` | Limite local de quota por instância do cliente nesta execução |
| `youtube.tentativas_requisicao` | Limite de tentativas por requisição |
| `datalake.diretorio_raiz` | Diretório das camadas, relativo a `--raiz` |
| `rag.estrategia_recuperacao` | `semantica` ou `hibrida` |
| `rag.recuperar_documentos` | Quantidade final desejada de documentos |
| `vetor.tabela` / `vetor.esquema` | Destino dos documentos e embeddings |
| `vetor.inicializar_tabela` | Permite criar a tabela quando ela não existe |
| `mlflow.uri_rastreamento` | URI do servidor; aceita expansão como `${MLFLOW_PORT}` |
| `observabilidade.arquivo_metricas` | Arquivo Prometheus, relativo a `--raiz` |

O canal atual é `UCoLf24olVUtKOsSXlqv_-ag`. Para vários canais, acrescente IDs na lista `youtube.ids_canais`.

A janela filtra a **publicação dos vídeos**, não a data dos comentários. Por exemplo, executando em 01/10/2026 com `dias_publicacao_atras: 2`, no fuso configurado:

- `dia_exato`: vídeos publicados em 29/09/2026;
- `acumulada`: vídeos publicados de 29/09/2026 até 01/10/2026, inclusive.

Os limites de página por recurso estão em `youtube.limites_paginas`. O limite global não substitui esses limites específicos. A quota local não consulta o saldo global da conta Google.

### Modelos e resposta

Edite [modelos_rag.yaml](../configuracao/modelos_rag.yaml).

| Etapa | Modelo atualmente configurado |
|---|---|
| Embeddings | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| Geração | `Qwen/Qwen2.5-0.5B-Instruct` |
| Reranking | `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` |

Os embeddings atuais têm `dimensoes: 384`. Ao trocar esse modelo, confira a dimensão e a compatibilidade da tabela vetorial. A inicialização preserva tabelas existentes; ela não migra automaticamente a dimensão de uma tabela já criada.

Para desligar o reranking, configure **ambos**:

- `rag.reranking_habilitado: false`, no YAML do projeto;
- `reranking.habilitado: false`, no YAML dos modelos.

Quando habilitado, o número final é o menor entre `rag.recuperar_documentos` e `reranking.quantidade_final`; `quantidade_candidatos` precisa comportar esse resultado. O prompt de contexto deve manter os campos `{pergunta}` e `{contexto}`.

## 5. Validar a configuração

```bash
PYTHONPATH=src .venv/bin/python -m pipeline_principal \
  --projeto configuracao/projeto_rag.yaml \
  --modelos configuracao/modelos_rag.yaml \
  --raiz . \
  --validar
```

Sucesso:

```json
{"estado": "configuracao_valida"}
```

Esse comando valida os YAMLs, as configurações operacionais e a presença de uma chave sem placeholder. Ele **não** autentica a chave na API, testa a conexão PostgreSQL/MLflow nem baixa modelos.

## 6. Coletar e indexar

```bash
PYTHONPATH=src .venv/bin/python -m pipeline_principal \
  --projeto configuracao/projeto_rag.yaml \
  --modelos configuracao/modelos_rag.yaml \
  --raiz .
```

O fluxo coleta os canais configurados, persiste Bronze/Prata/Ouro e indexa os documentos quando houver conteúdo. Sem pergunta, não imprime uma resposta final. Os logs acompanham as etapas; código de saída `0` indica sucesso.

A composição atual também carrega o modelo de geração e o reranker habilitado ao preparar o serviço, mesmo sem pergunta. Se nenhum documento for encontrado na janela, o fluxo termina antes de carregar os modelos.

## 7. Fazer perguntas

```bash
PYTHONPATH=src .venv/bin/python -m pipeline_principal \
  --projeto configuracao/projeto_rag.yaml \
  --modelos configuracao/modelos_rag.yaml \
  --raiz . \
  --pergunta 'Quais são as principais dúvidas nos comentários?' \
  --canal UCoLf24olVUtKOsSXlqv_-ag
```

Para restringir a recuperação a um vídeo, acrescente `--video` com o ID desejado. Esses filtros atuam na **recuperação**; a coleta continua usando os canais e a janela do YAML.

Cada execução com pergunta realiza novamente coleta, preparação e indexação. A CLI atual não oferece um modo de consulta independente da coleta.

A resposta é um objeto JSON com:

- `resposta`: texto gerado ou mensagem configurada de evidência insuficiente;
- `fontes`: documentos recuperados, conteúdo e metadados de proveniência.

Os logs estruturados usam a saída de logging padrão; o JSON final é escrito em stdout. Para salvar a resposta, acrescente `> resposta.json` ao comando. Em caso de falha, esse arquivo conterá o JSON de erro.

Se a coleta atual estiver vazia, a execução retorna a mensagem sem evidências antes de consultar o índice, mesmo que existam documentos indexados anteriormente.

### Exemplo de resultado com fontes

Para a pergunta “Quais são as principais dúvidas nos comentários?”, uma saída ilustrativa seria:

**Dados fictícios:** este exemplo demonstra o formato da CLI. Não foi coletado do canal configurado nem gerado pelo modelo. IDs e URL de proveniência são ilustrativos.

```json
{
  "resposta": "A dúvida apresentada é como instalar a biblioteca [comentario_sintetico_1].",
  "fontes": [
    {
      "documento_id": "comentario_sintetico_1",
      "conteudo": "Não consegui instalar a biblioteca. Como faço?",
      "metadados": {
        "canal_id": "canal_sintetico",
        "video_id": "video_sintetico",
        "comentario_id": "comentario_sintetico_1",
        "comentario_pai_id": null,
        "data_publicacao": "2026-09-29T14:00:00+00:00",
        "data_atualizacao": "2026-09-29T14:00:00+00:00",
        "data_ingestao": "2026-10-01T15:00:00+00:00",
        "quantidade_likes": 3,
        "tipo_documento": "comentario",
        "fonte": "https://www.youtube.com/watch?v=video_sintetico&lc=comentario_sintetico_1"
      }
    }
  ]
}
```

A citação `[comentario_sintetico_1]` aponta para `fontes[0].documento_id`. O conteúdo apresenta a evidência recuperada; os metadados permitem identificar canal, vídeo, comentário e datas. Em uma execução real, `fonte` aponta para o comentário de origem. A redação gerada pode variar.

O JSON completo também está em [exemplo_resposta.json](../production_artifacts/exemplo_resposta.json).

### Exemplo sem evidências

Quando não há documentos na coleta atual ou a recuperação não encontra fontes para os filtros, a saída segue este formato, usando a mensagem configurada no YAML:

```json
{
  "resposta": "Não há evidências suficientes nos comentários coletados.",
  "fontes": []
}
```

Disponível também em [exemplo_sem_contexto.json](../production_artifacts/exemplo_sem_contexto.json). Nesse caso, a aplicação não chama o modelo para gerar a resposta.

## 8. Encontrar os resultados e acompanhar as etapas

Com os caminhos atuais, os resultados ficam em:

| Local | Conteúdo |
|---|---|
| `data_lake/bronze/` | Payloads brutos e metadados de coleta |
| `data_lake/prata/` | Comentários normalizados e deduplicados por lote |
| `data_lake/ouro/` | Documentos com proveniência para o RAG |
| PostgreSQL, tabela configurada | Documentos, embeddings e metadados consultáveis |
| `production_artifacts/metricas_pipeline.prom` | Métricas da execução mais recente que alcançou a etapa instrumentada |
| Experimento MLflow configurado | Traces e etapas instrumentadas |

O lake grava arquivos JSONL por lote. Reexecuções podem gerar novos arquivos; o índice utiliza IDs estáveis para atualizar os documentos correspondentes. A busca lexical usa os documentos do lote atual, enquanto a busca semântica consulta o índice persistido.

Na configuração do Compose consultada, Grafana publica a porta `3000` e Prometheus a porta `9090`; a porta do MLflow vem de `.env`. O exportador de métricas é consultado pelo Prometheus na rede interna. Se mudar o caminho do arquivo de métricas no YAML, mantenha o volume e o caminho de leitura do exportador coerentes no Compose existente.

Para investigar serviços específicos:

```bash
docker compose logs --tail 50 mlflow
docker compose logs --tail 50 grafana
docker compose logs --tail 50 prometheus
docker compose logs --tail 50 metricas-treino
```

Consulte logs localmente e revise dados sensíveis antes de compartilhá-los.

## 9. Executar validações

As validações locais não precisam da chave YouTube nem de downloads dos modelos:

```bash
.venv/bin/pytest -q
.venv/bin/mypy src
.venv/bin/ruff check src tests
docker compose config --quiet
```

Para testar o PGVectorStore no banco real:

```bash
RAG_TESTE_PROJETO=configuracao/projeto_rag.yaml \
RAG_TESTE_MODELOS=configuracao/modelos_rag.yaml \
RAG_TESTE_RAIZ=. \
RAG_TESTE_TABELA=validacao_rag_contrato \
.venv/bin/pytest -q tests/testes_integracao/teste_pgvector.py
```

Escolha uma tabela de teste exclusiva, inexistente e diferente da tabela de produção. O teste cria essa tabela, usa embeddings determinísticos e a remove ao terminar. Ele verifica a integração com o banco, não a qualidade dos modelos Hugging Face.

O dataset [dataset_rag_v1.jsonl](../avaliacoes/dataset_rag_v1.jsonl) contém exemplos sintéticos. A avaliação GenAI exige chamada Python a `AvaliadorGenai.avaliar_dataset`, dataset com evidências e scorers explícitos para `retrieval`, `geracao` e `completo`; não há comando CLI de avaliação. Retornar fontes não comprova, por si só, a factualidade da resposta.

## 10. Resolver problemas comuns

| Sintoma | O que conferir |
|---|---|
| `--validar` retorna `ValueError` | Arquivo `youtube.env`, chave sem placeholder, modelos/canais configurados e flags de reranking iguais |
| `ValidationError` | Chaves desconhecidas, valores inválidos, limites de página, pesos, timezone e formato dos prompts nos YAMLs |
| Falha durante acesso ao YouTube | API habilitada, chave válida, permissões/restrições da chave, rede e quota |
| Nenhum documento ou resposta sem evidências | Datas dos vídeos, janela e timezone; comentários disponíveis; filtros de recuperação |
| Erro de conexão PostgreSQL | Serviço saudável, variáveis de `.env`, conexão exportada no terminal e host/porta no YAML |
| Erro de dimensão dos embeddings | Modelo, dimensão configurada e dimensão da tabela existente |
| Erro ao carregar modelos | Extra `modelos` instalado, internet, memória e dispositivo configurado |
| Falha MLflow | Serviço saudável, `MLFLOW_PORT` definida e URI expandida corretamente |
| Grafana reiniciando ou `unhealthy` | Logs, permissões do volume e conclusão das migrações antes de avaliar disponibilidade |
| Métricas vazias | Execução alcançou as etapas instrumentadas; arquivo gerado e caminho do exportador coincidem |

A CLI retorna código `1` em caso de erro. Para arquivo YouTube ausente ou chave vazia/placeholder, inclui `codigo` e `orientacao` com instruções seguras. Exceções de fornecedores continuam exibindo somente o tipo para evitar exposição de credenciais. Os relatórios em [production_artifacts](../production_artifacts/) descrevem verificações anteriores; confirme o estado atual com `docker compose ps`.

## 11. Abrir o dashboard RAG no Grafana

Acesse [RAG de Comentários do YouTube](http://localhost:3000/d/rag-comentarios-youtube/rag-de-comentarios-do-youtube), usando a porta publicada pelo Compose existente. Também é possível procurar esse título em **Dashboards**, sem restringir a busca a favoritos.

O painel inclui saúde do exportador, comentários coletados, documentos indexados, contagens das camadas, erros, duração das etapas e métricas de qualidade publicadas. Se o pipeline ainda não gerou `production_artifacts/metricas_pipeline.prom`, os painéis RAG ficam **Sem dados**. O exportador pode estar disponível mesmo sem esse arquivo.

A seção **Dataset v1 — exemplos sintéticos** mostra perguntas, respostas esperadas e evidências de `avaliacoes/dataset_rag_v1.jsonl`. Essa prévia não constitui uma avaliação executada e não publica scores. O JSONL é um dataset; o dashboard provisionável é `config_ob/dashboards/dashboard_comentarios.json`.

O arquivo de métricas mantém um snapshot por execução: contadores reiniciam a cada execução e a mesma amostra é servida até ser substituída. Por isso o dashboard apresenta contagens absolutas e durações médias do snapshot, em vez de taxas de um serviço contínuo.

Para atualizar a prévia depois de editar o dataset, ou atualizar o namespace depois de editar o YAML do projeto:

```bash
PYTHONPATH=src .venv/bin/python -m observabilidade_app.gerador_dashboard \
  --configuracao configuracao/dashboard_rag.yaml \
  --raiz .
```

O modelo do painel, UID da fonte, caminhos e parâmetros visuais ficam em `configuracao/dashboard_rag.yaml`. O namespace e o timezone vêm do YAML do projeto. O provider existente carrega o JSON do diretório montado; consulte a [documentação de provisionamento do Grafana](https://grafana.com/docs/grafana/latest/administration/provisioning/) para o comportamento de atualização por arquivo. Edite o YAML e regenere o JSON para manter a alteração persistente.

## 12. Gerar respostas pela API MLflow `/invocations`

O serviço `mlflow-serving` do Compose existente agora atende o RAG usando o servidor oficial [MLflow Model Serving](https://mlflow.org/docs/latest/ml/deployment/deploy-model-locally/). A publicação captura os documentos Ouro e os YAMLs; a inferência consulta esse snapshot e o índice vetorial existente, sem refazer a coleta ou indexação por pergunta.

### Publicar ou atualizar o modelo

Depois de executar a ingestão/indexação, publique o snapshot:

```bash
PYTHONPATH=src .venv/bin/python -m integracao_mlflow.publicador_modelo \
  --configuracao configuracao/servico_rag.yaml --raiz .
```

A publicação usa a API do MLflow e grava `production_artifacts/modelo_publicado.json`, `modelo_serving.uri` e `requisitos_serving.txt`. Não inclui `.env` ou `youtube.env` nos artefatos. Não exige a chave YouTube, pois utiliza o Ouro já preparado. O snapshot inicialmente vazio continua válido, mas responde sem evidências até uma nova publicação com documentos.

### Iniciar o serviço existente

```bash
docker compose up -d --no-deps mlflow-serving metricas-treino
docker compose logs --tail 30 mlflow-serving
```

O serviço usa Python 3.12, instala PyTorch CPU e as dependências declaradas no YAML. O primeiro início pode demorar. Pesos Hugging Face são carregados quando o snapshot tem documentos; os caches ficam nos volumes de dependências/modelos configurados no Compose.

Depois de republicar um modelo, reinicie o serviço para ler a nova URI:

```bash
docker compose restart mlflow-serving
```

### Enviar uma pergunta

Na porta atualmente publicada pelo Compose:

```bash
curl --fail-with-body http://localhost:8080/invocations \
  -H 'Content-Type: application/json' \
  -d '{"inputs":[{"pergunta":"Quais são as principais dúvidas nos comentários?","canal_id":"UCoLf24olVUtKOsSXlqv_-ag"}]}'
```

O formato `inputs` corresponde à assinatura do modelo: lista de objetos com campos textuais. Cada objeto exige `pergunta` não vazia; `canal_id` e `video_id` são filtros opcionais. Várias perguntas podem ser enviadas na mesma lista. A resposta HTTP contém `predictions`, com uma resposta/fontes para cada pergunta, na mesma ordem.

Exemplo quando o snapshot não contém documentos:

```json
{
  "predictions": [
    {
      "resposta": "Não há evidências suficientes nos comentários coletados.",
      "fontes": []
    }
  ]
}
```

Quando houver documentos, o resultado em `predictions` tem o mesmo formato de resposta/fontes mostrado na seção 7, usando retrieval, reranking habilitado e geração Hugging Face reais. Para habilitar esse caminho, prepare o Ouro e o índice pelo pipeline e republique o modelo.

A configuração de publicação/serving fica em `configuracao/servico_rag.yaml`: nome, artefatos, requisitos, índice CPU, host, porta, workers e timeout. A conexão do banco e a URI de tracking vêm do ambiente do contêiner, usando os serviços já definidos. Se alterar porta/host, mantenha publicação e healthcheck coerentes no Compose.

As requisições publicam traces no experimento de serving configurado. As métricas ficam em `production_artifacts/metricas_serving.prom`, com namespace separado das métricas de ingestão, e são lidas pelo exportador existente. Contagens do serving acumulam durante a vida do processo; reiniciar o serviço reinicia essas contagens.
