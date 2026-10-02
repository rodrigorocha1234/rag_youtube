import pytest

from documentos_rag.documento_rag import DocumentoRag
from geracao_resposta.servico_resposta import ServicoResposta
from recuperacao_rag.busca_lexical import BuscaLexical
from recuperacao_rag.estrategia_hibrida import EstrategiaHibrida
from recuperacao_rag.registro_estrategias import RegistroEstrategias


def criar_documento(chave: str, texto: str, canal: str) -> DocumentoRag:
    return DocumentoRag(documento_id=chave, conteudo=texto, metadados={"canal_id": canal, "video_id": "video", "data_publicacao": "2026-09-29"})


def test_filtros_preservam_proveniencia() -> None:
    documento = criar_documento("a", "python moderno", "canal")
    fonte = BuscaLexical([documento, criar_documento("b", "python", "outro")])
    assert fonte.buscar_documentos("python", 5, {"canal_id": "canal", "video_id": "video", "data_publicacao": "2026-09-29"}) == [documento]
    assert fonte.buscar_documentos("python", 5, {"video_id": "ausente"}) == []


def test_fusao_elimina_duplicados_e_respeita_filtros() -> None:
    documentos = [criar_documento("a", "python", "canal"), criar_documento("b", "python moderno", "outro")]
    fonte = BuscaLexical(documentos)
    busca = EstrategiaHibrida(fonte, fonte, 1, 1, 60)
    assert busca.buscar_documentos("python", 5, {"canal_id": "canal"}) == [documentos[0]]
    with pytest.raises(ValueError):
        RegistroEstrategias({"hibrida": busca}).obter_estrategia("inexistente")


def test_ausencia_contexto_nao_invoca_modelo() -> None:
    class GeradorFalha:
        def gerar_texto(self, prompt: str) -> str:
            raise AssertionError("Modelo não deve gerar sem contexto")
    servico = ServicoResposta(BuscaLexical([]), GeradorFalha(), 5, 3, "{contexto} {pergunta}", "Sem evidências")
    resposta = servico.responder_pergunta("pergunta", {})
    assert resposta.texto == "Sem evidências"
    assert resposta.fontes == ()
    assert not resposta.tem_contexto


def test_reranking_e_fontes_usam_documentos_finais() -> None:
    class GeradorCaptura:
        prompt = ""
        def gerar_texto(self, prompt: str) -> str:
            self.prompt = prompt
            return "Resposta [b]"
    class RerankingReverso:
        def ordenar_documentos(self, pergunta: str, documentos: list[DocumentoRag]) -> list[DocumentoRag]:
            return list(reversed(documentos))
    documentos = [criar_documento("a", "python", "canal"), criar_documento("b", "python moderno", "canal")]
    gerador = GeradorCaptura()
    servico = ServicoResposta(BuscaLexical(documentos), gerador, 5, 1, "{contexto}\n{pergunta}", "Vazio", RerankingReverso())
    resposta = servico.responder_pergunta("python", {})
    assert resposta.fontes == (documentos[1],)
    assert "[b]" in gerador.prompt
    assert "[a]" not in gerador.prompt


def test_intervalo_datas_inclusivo() -> None:
    documento = criar_documento("a", "python", "canal")
    fonte = BuscaLexical([documento])
    assert fonte.buscar_documentos("python", 5, {"data_publicacao": {"$gte": "2026-09-28", "$lte": "2026-09-29"}}) == [documento]
    assert fonte.buscar_documentos("python", 5, {"data_publicacao": {"$gt": "2026-09-29"}}) == []
    with pytest.raises(ValueError):
        fonte.buscar_documentos("python", 5, {"data_publicacao": {"$invalid": "2026-09-29"}})


def test_topk_maior_que_candidatos_falha_cedo() -> None:
    class GeradorDuplo:
        def gerar_texto(self, prompt: str) -> str:
            return prompt
    with pytest.raises(ValueError):
        ServicoResposta(BuscaLexical([]), GeradorDuplo(), 2, 3, "{contexto}", "Vazio")
