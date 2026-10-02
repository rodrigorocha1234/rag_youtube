"""Auditoria estática das regras estruturais obrigatórias."""

import ast
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
FONTES = tuple((RAIZ / "src").rglob("*.py"))


@pytest.mark.parametrize("arquivo", FONTES, ids=lambda caminho: caminho.name)
def test_contrato_arquitetural(arquivo: Path) -> None:
    assert arquivo.name in {"__init__.py", "__main__.py"} or re.fullmatch(
        r"[a-z]+_[a-z]+\.py", arquivo.name
    ), arquivo
    for parte in arquivo.relative_to(RAIZ / "src").parts[:-1]:
        assert re.fullmatch(r"[a-z]+_[a-z]+", parte), parte
        assert parte not in sys.stdlib_module_names
    arvore = ast.parse(arquivo.read_text())
    principais = []
    for no in ast.walk(arvore):
        assert not (isinstance(no, ast.Name) and no.id == "Any"), arquivo
        assert not (isinstance(no, ast.Attribute) and no.attr == "Any"), arquivo
        if isinstance(no, ast.ImportFrom) and no.module == "typing":
            assert all(alias.name not in {"Any", "*"} for alias in no.names)
        if isinstance(no, ast.Call) and isinstance(no.func, ast.Attribute):
            assert no.func.attr not in {"iterrows", "itertuples"}, arquivo
        if isinstance(no, ast.Raise) and isinstance(no.exc, ast.Call):
            assert not (
                isinstance(no.exc.func, ast.Name) and no.exc.func.id == "NotImplementedError"
            )
    for no in arvore.body:
        if isinstance(no, ast.ClassDef):
            bases = {ast.unparse(base) for base in no.bases}
            decoradores = {ast.unparse(dec).split("(")[0] for dec in no.decorator_list}
            if (
                not bases.intersection(
                    {
                        "TypedDict",
                        "Enum",
                        "StrEnum",
                        "Exception",
                        "ValueError",
                        "RuntimeError",
                        "BaseModel",
                        "ConfiguracaoBase",
                    }
                )
                and "dataclass" not in decoradores
            ):
                principais.append(no.name)
    assert len(principais) <= 1, (arquivo, principais)


def test_compose_unico() -> None:
    nomes = {"compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml"}
    assert [p.name for p in RAIZ.iterdir() if p.name in nomes] == ["docker-compose.yml"]


def test_segredos_ignorados() -> None:
    ignorados = (RAIZ / ".gitignore").read_text().splitlines()
    assert ".env" in ignorados and "youtube.env" in ignorados
