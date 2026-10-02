"""Filtros de igualdade e intervalos compatíveis com PGVectorStore."""
from collections.abc import Callable
from datetime import datetime, timezone
from operator import eq, ge, gt, le, lt, ne
from typing import cast

from recuperacao_rag.contratos_busca import FiltrosBusca, ValorFiltro

_OPERADORES: dict[str, Callable[[object, object], bool]] = {
    "$eq": eq, "$ne": ne,
    "$gte": cast(Callable[[object, object], bool], ge),
    "$gt": cast(Callable[[object, object], bool], gt),
    "$lte": cast(Callable[[object, object], bool], le),
    "$lt": cast(Callable[[object, object], bool], lt),
}


def verificar_filtros(metadados: dict[str, ValorFiltro], filtros: FiltrosBusca) -> bool:
    for campo, condicao in filtros.items():
        operadores = condicao if isinstance(condicao, dict) else {"$eq": condicao}
        for operador, esperado in operadores.items():
            if operador not in _OPERADORES:
                raise ValueError(f"Operador de filtro inválido: {operador}")
            atual = metadados.get(campo)
            if campo.startswith("data_") and isinstance(atual, str) and isinstance(esperado, str):
                resultado = _OPERADORES[operador](_converter_data(atual), _converter_data(esperado))
            else:
                try:
                    resultado = _OPERADORES[operador](atual, esperado)
                except TypeError:
                    resultado = False
            if not resultado:
                return False
    return True


def converter_filtros(filtros: FiltrosBusca) -> dict[str, object]:
    condicoes: list[dict[str, object]] = []
    for campo, condicao in filtros.items():
        operadores = condicao if isinstance(condicao, dict) else {"$eq": condicao}
        for operador, valor in operadores.items():
            if operador not in _OPERADORES:
                raise ValueError(f"Operador de filtro inválido: {operador}")
            condicoes.append({campo: {operador: valor}})
    if len(condicoes) == 1:
        return condicoes[0]
    return {"$and": condicoes} if condicoes else {}


def _converter_data(valor: str) -> datetime:
    data = datetime.fromisoformat(valor.replace("Z", "+00:00"))
    return data.replace(tzinfo=timezone.utc) if data.tzinfo is None else data.astimezone(timezone.utc)
