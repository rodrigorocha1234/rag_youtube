"""Contratos locais de observabilidade; nenhum serviço remoto é simulado como real."""
import logging

import pytest

from integracao_mlflow.avaliador_genai import AvaliadorGenai
from integracao_mlflow.tracador_mlflow import TracadorMlflow
from observabilidade_app.monitor_operacao import MonitorOperacao
from testes_integracao.genai_duplo import GenaiDuplo
from testes_integracao.sdk_duplo import SdkDuplo


def test_metricas_e_logs_sem_segredo(caplog: pytest.LogCaptureFixture) -> None:
    monitor = MonitorOperacao("teste", (0.1, 1.0), ("valor_secreto",))
    with caplog.at_level(logging.INFO):
        with monitor.envolver_etapa("retrieval", {"api_key": "valor_secreto", "consulta": "texto valor_secreto"}):
            monitor.registrar_contagem("quota", 2)
            monitor.registrar_qualidade("mrr", 0.5)
        with pytest.raises(ValueError):
            with monitor.envolver_etapa("geracao"):
                raise ValueError("valor_secreto")
    assert "valor_secreto" not in caplog.text
    assert "api_key" not in caplog.text
    metricas = monitor.exportar_metricas().decode()
    assert 'teste_eventos_total{etapa="quota"} 2.0' in metricas
    assert 'teste_erros_total{etapa="geracao",tipo="ValueError"} 1.0' in metricas
    assert 'teste_qualidade{criterio="mrr"} 0.5' in metricas


def test_traces_nao_expoem_erro_do_provedor() -> None:
    sdk = SdkDuplo()
    tracador = TracadorMlflow(True, "uri_teste", "experimento_teste", ("valor_secreto",), sdk)
    with pytest.raises(ValueError):
        with tracador.envolver_etapa("geracao", {"consulta": "valor_secreto"}) as saidas:
            saidas["resposta"] = "valor_secreto"
            raise ValueError("valor_secreto")
    assert sdk.span.entradas == {"consulta": "[REDACTED]"}
    assert sdk.span.saidas == {"resposta": "[REDACTED]"}
    assert sdk.span.atributos == {"estado": "erro", "tipo_erro": "ValueError"}
    assert sdk.span.estado == "ERROR"
    assert not sdk.excecoes


def test_avaliacao_genai_exige_tres_escopos() -> None:
    sdk = GenaiDuplo()
    avaliador = AvaliadorGenai(sdk)
    resultados = avaliador.avaliar_dataset([{"inputs": {"pergunta": "teste"}}], {"retrieval": [object()], "geracao": [object()], "completo": [object()]})
    assert set(resultados) == {"retrieval", "geracao", "completo"}
    assert sdk.chamadas == 3
    with pytest.raises(ValueError):
        avaliador.avaliar_dataset([], {})
