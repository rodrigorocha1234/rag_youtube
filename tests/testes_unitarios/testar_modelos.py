from dominio_youtube.modelos_dominio import EscopoRecuperacao


def testar_escopos_recuperacao() -> None:
    assert EscopoRecuperacao.CANAL.value == "canal"
    assert EscopoRecuperacao.VIDEO.value == "video"
    assert EscopoRecuperacao.CANAL_VIDEO.value == "canal_video"
