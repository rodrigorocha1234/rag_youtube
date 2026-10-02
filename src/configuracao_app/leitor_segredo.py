import os


class LeitorSegredo:
    def obter_segredo(self, nome: str) -> str:
        valor = os.environ.get(nome)
        if not valor:
            raise RuntimeError(f"Segredo obrigatório ausente: {nome}")
        return valor
