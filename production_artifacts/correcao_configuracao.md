# Correção da validação YouTube

Causa identificada: youtube.env ausente, enquanto YOUTUBE_API_KEY já estava disponível em .env. Copiada somente essa variável para o arquivo configurado, criado com permissão 0600 e ignorado pelo versionamento. Nenhum valor foi exibido ou registrado.

--validar executado com os YAMLs reais: estado configuracao_valida. Isso valida presença/configuração local, sem confirmar autorização da chave pela API Google.

CLI agora informa codigo e orientacao para arquivo ausente/chave inválida. Exceções não controladas continuam mostrando só tipo, sem mensagens de fornecedores. Testes cobrem arquivo ausente, chave vazia/placeholder e não divulgação de mensagem sensível.

QA: 106 testes aprovados, 1 integração externa ignorada; mypy strict 61 fontes e Ruff aprovados. Nenhuma coleta ou inferência real executada nesta correção.
