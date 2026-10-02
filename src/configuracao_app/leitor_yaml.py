from pathlib import Path
from collections.abc import Mapping
import os
import re
import yaml


class LeitorYaml:
    _padrao_variavel = re.compile(r"\$\{([A-Z0-9_]+)\}")

    def carregar_configuracao(self, caminho: Path) -> Mapping[str, object]:
        conteudo = caminho.read_text(encoding="utf-8")
        resolvido = self._padrao_variavel.sub(lambda m: os.environ.get(m.group(1), m.group(0)), conteudo)
        dados = yaml.safe_load(resolvido)
        if not isinstance(dados, dict):
            raise ValueError("Configuração YAML deve possuir objeto raiz.")
        return dados
