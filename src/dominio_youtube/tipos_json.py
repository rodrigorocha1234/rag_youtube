"""Tipos recursivos e validação de payloads externos."""

from typing import TypeAlias

ValorJson: TypeAlias = str | int | float | bool | None | list["ValorJson"] | dict[str, "ValorJson"]
ObjetoJson: TypeAlias = dict[str, ValorJson]


def validar_json(valor: object) -> ValorJson:
    if valor is None or isinstance(valor, (str, int, float, bool)):
        return valor
    if isinstance(valor, list):
        return [validar_json(item) for item in valor]
    if isinstance(valor, dict):
        return {str(chave): validar_json(item) for chave, item in valor.items()}
    raise ValueError("Valor inválido no JSON")


def obter_objeto(valor: ValorJson) -> ObjetoJson:
    if not isinstance(valor, dict):
        raise ValueError("Objeto JSON esperado")
    return valor


def obter_texto(valor: ValorJson) -> str:
    if not isinstance(valor, str):
        raise ValueError("Texto JSON esperado")
    return valor
