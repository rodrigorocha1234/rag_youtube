"""Limpeza e deduplicação vetorizadas."""

import pandas as pd

from dominio_youtube.comentario_youtube import ComentarioYoutube


class NormalizadorTexto:
    def normalizar_registros(self, registros: list[ComentarioYoutube]) -> list[ComentarioYoutube]:
        if not registros:
            return []
        quadro = pd.DataFrame([item.model_dump() for item in registros])
        quadro = quadro.assign(
            texto_normalizado=quadro["texto_original"]
            .str.normalize("NFKC")
            .str.replace(r"<[^>]+>", " ", regex=True)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )
        quadro = quadro.sort_values("data_atualizacao").drop_duplicates(
            "comentario_id", keep="last"
        )
        quadro = quadro.loc[quadro["texto_normalizado"].ne("")]
        quadro = quadro.astype(object).where(pd.notna(quadro), None)
        # Conversão na fronteira de serialização; processamento acima é vetorizado.
        return [ComentarioYoutube.model_validate(item) for item in quadro.to_dict(orient="records")]
