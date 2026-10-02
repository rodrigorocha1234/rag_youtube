"""CLI explícita, sem caminhos operacionais predefinidos."""

import argparse
import json
from pathlib import Path

from configuracao_app.carregador_config import CarregadorConfig
from configuracao_app.erro_configuracao import ErroConfiguracao
from pipeline_principal.execucao_pipeline import ExecucaoPipeline
from recuperacao_rag.contratos_busca import FiltrosBusca


def executar_comando() -> int:
    parser = argparse.ArgumentParser(description="RAG de comentários YouTube")
    parser.add_argument("--projeto", type=Path, required=True)
    parser.add_argument("--modelos", type=Path, required=True)
    parser.add_argument("--raiz", type=Path, required=True)
    parser.add_argument("--validar", action="store_true")
    parser.add_argument("--pergunta")
    parser.add_argument("--canal")
    parser.add_argument("--video")
    args = parser.parse_args()
    try:
        projeto = CarregadorConfig.carregar_projeto(args.projeto)
        modelos = CarregadorConfig.carregar_modelos(args.modelos)
        CarregadorConfig.validar_operacao(projeto, modelos)
        CarregadorConfig.carregar_segredo(projeto, args.raiz)
        if args.validar:
            print(json.dumps({"estado": "configuracao_valida"}))
            return 0
        filtros: FiltrosBusca = {}
        if args.canal:
            filtros["canal_id"] = args.canal
        if args.video:
            filtros["video_id"] = args.video
        resposta = ExecucaoPipeline(projeto, modelos, args.raiz).executar_fluxo(
            args.pergunta, filtros
        )
        if resposta is not None:
            print(
                json.dumps(
                    {
                        "resposta": resposta.texto,
                        "fontes": [doc.model_dump() for doc in resposta.fontes],
                    },
                    ensure_ascii=False,
                )
            )
        return 0
    except ErroConfiguracao as erro:
        print(
            json.dumps(
                {
                    "estado": "falha",
                    "tipo": type(erro).__name__,
                    "codigo": erro.codigo,
                    "orientacao": erro.orientacao,
                },
                ensure_ascii=False,
            )
        )
        return 1
    except Exception as erro:
        # Mensagens de provedores e validação podem conter credenciais: só tipo é público.
        print(json.dumps({"estado": "falha", "tipo": type(erro).__name__}))
        return 1


if __name__ == "__main__":
    raise SystemExit(executar_comando())
