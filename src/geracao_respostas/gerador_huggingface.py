from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEndpoint


class GeradorHuggingface:
    def __init__(self, modelo: str, temperatura: float, maximo_tokens: int, template: str) -> None:
        self._prompt = PromptTemplate.from_template(template)
        self._modelo = HuggingFaceEndpoint(
            repo_id=modelo, temperature=temperatura, max_new_tokens=maximo_tokens
        )

    def gerar_resposta(self, pergunta: str, contexto: str) -> str:
        return self._modelo.invoke(self._prompt.format(pergunta=pergunta, contexto=contexto))
