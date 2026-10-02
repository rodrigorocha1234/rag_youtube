"""Composição de recuperação, reranking e geração com proveniência."""
from contextlib import nullcontext

from documentos_rag.documento_rag import DocumentoRag
from geracao_resposta.contrato_gerador import GeradorTexto
from geracao_resposta.resposta_fontes import RespostaFontes
from integracao_mlflow.tracador_mlflow import TracadorMlflow
from observabilidade_app.monitor_operacao import MonitorOperacao
from recuperacao_rag.contrato_reranking import ModeloReranking
from recuperacao_rag.contratos_busca import FiltrosBusca, FonteBusca


class ServicoResposta:
    def __init__(self, busca: FonteBusca, gerador: GeradorTexto, quantidade_candidatos: int,
                 quantidade_final: int, prompt_contexto: str, resposta_vazia: str,
                 reranking: ModeloReranking | None = None, monitor: MonitorOperacao | None = None,
                 tracador: TracadorMlflow | None = None) -> None:
        if quantidade_final <= 0 or quantidade_candidatos < quantidade_final:
            raise ValueError("Quantidades de recuperação inválidas")
        self.busca = busca
        self.gerador = gerador
        self.quantidade_candidatos = quantidade_candidatos
        self.quantidade_final = quantidade_final
        self.prompt_contexto = prompt_contexto
        self.resposta_vazia = resposta_vazia
        self.reranking = reranking
        self.monitor = monitor
        self.tracador = tracador

    def responder_pergunta(self, pergunta: str, filtros: FiltrosBusca) -> RespostaFontes:
        with (self.monitor.envolver_etapa("recuperar_documentos") if self.monitor else nullcontext()), (
                self.tracador.envolver_etapa("recuperar_documentos") if self.tracador else nullcontext()):
            documentos = self.busca.buscar_documentos(pergunta, self.quantidade_candidatos, filtros)
            if self.monitor:
                self.monitor.registrar_contagem("documentos_recuperados", len(documentos))
        if self.reranking is not None:
            documentos = self.reranking.ordenar_documentos(pergunta, documentos)
        documentos = documentos[:self.quantidade_final]
        if not documentos:
            return RespostaFontes(self.resposta_vazia, (), False)
        contexto = self.montar_contexto(documentos)
        with (self.monitor.envolver_etapa("gerar_resposta") if self.monitor else nullcontext()), (
                self.tracador.envolver_etapa("gerar_resposta") if self.tracador else nullcontext()):
            texto = self.gerador.gerar_texto(self.prompt_contexto.format(pergunta=pergunta, contexto=contexto))
        return RespostaFontes(texto, tuple(documentos), True)

    @staticmethod
    def montar_contexto(documentos: list[DocumentoRag]) -> str:
        return "\n\n".join(f"[{doc.documento_id}] {doc.conteudo}" for doc in documentos)
