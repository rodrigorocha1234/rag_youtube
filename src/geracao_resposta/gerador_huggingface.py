"""Geração local por LangChain HuggingFacePipeline."""

class GeradorHuggingface:
    def __init__(self, modelo: str, tarefa: str, dispositivo: int, temperatura: float, max_tokens: int) -> None:
        from langchain_huggingface import HuggingFacePipeline
        self.modelo = HuggingFacePipeline.from_model_id(
            model_id=modelo, task=tarefa, device=dispositivo,
            pipeline_kwargs={"temperature": temperatura, "max_new_tokens": max_tokens,
                             "do_sample": temperatura > 0, "return_full_text": False})

    def gerar_texto(self, prompt: str) -> str:
        return self.modelo.invoke(prompt)
