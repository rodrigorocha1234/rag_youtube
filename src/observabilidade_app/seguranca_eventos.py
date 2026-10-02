"""Sanitização compartilhada por logs e traces."""

from collections.abc import Mapping

ValorEvento = str | int | float | bool | None


def limpar_eventos(
    eventos: Mapping[str, ValorEvento], segredos: tuple[str, ...]
) -> dict[str, ValorEvento]:
    """Remove campos sensíveis e mascara valores secretos conhecidos."""
    resultado: dict[str, ValorEvento] = {}
    for chave, valor in eventos.items():
        if any(
            termo in chave.lower()
            for termo in (
                "secret",
                "segredo",
                "token",
                "password",
                "senha",
                "api_key",
                "authorization",
            )
        ):
            continue
        if isinstance(valor, str):
            for segredo in segredos:
                if segredo:
                    valor = valor.replace(segredo, "[REDACTED]")
        resultado[chave] = valor
    return resultado


def limpar_valor(valor: object, segredos: tuple[str, ...]) -> object:
    """Sanitiza estruturas JSON de datasets antes da avaliação."""
    if isinstance(valor, str):
        for segredo in segredos:
            if segredo:
                valor = valor.replace(segredo, "[REDACTED]")
        return valor
    if isinstance(valor, Mapping):
        resultado: dict[str, object] = {}
        for chave, item in valor.items():
            if not isinstance(chave, str):
                raise ValueError("Dataset requer chaves textuais")
            if limpar_eventos({chave: None}, segredos):
                resultado[chave] = limpar_valor(item, segredos)
        return resultado
    if isinstance(valor, (list, tuple)):
        return [limpar_valor(item, segredos) for item in valor]
    if valor is None or isinstance(valor, (bool, int, float)):
        return valor
    raise ValueError("Dataset requer valores JSON sanitizáveis")
