"""Teste de arquitetura — trava a tabela "Regras de dependência" de `docs/01`.

Percorre `src/**/*.py` com `ast`, extrai cada `import` / `from ... import`,
classifica o módulo numa camada e falha se algum import cruzar uma fronteira que
a arquitetura proíbe:

* `domain`               → só stdlib;
* `application.ports`     → `domain` (+ stdlib / `typing`);
* `application.use_cases` → `domain` + `application.ports`;
* `infrastructure.*`      → `domain` + `application` + `settings` + libs externas,
  **nunca** `interfaces` nem a *composition root* (`container` / `main`);
* `interfaces.*`          → `application` + `container` + `settings` + `fastapi` + stdlib;
* `container` / `main`    → livre;
* `logging_config`        → só stdlib; importável por qualquer camada.

Reforça, num teste dedicado, o princípio 3 do doc 01: `httpx`, `redis`,
`telegram`, `langgraph` e `langchain*` são proibidos em `domain` e `application`.

Um import proibido introduzido de propósito faz o teste falhar apontando o
módulo, a linha e o import ofensor.
"""

from __future__ import annotations

import ast
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

_ROOT_PACKAGE = "src"
_SRC = Path(__file__).resolve().parent.parent / _ROOT_PACKAGE

# --- camadas -----------------------------------------------------------------

_DOMAIN = "domain"
_PORTS = "application.ports"
_USE_CASES = "application.use_cases"
_APPLICATION = "application"  # o pacote raiz de `application` (hoje só o __init__)
_INFRA = "infrastructure"
_INTERFACES = "interfaces"
_CONTAINER = "container"
_MAIN = "main"
_SETTINGS = "settings"
_LOGGING = "logging_config"  # `src/logging_config.py` — cross-cutting, só stdlib
_ROOT = "root"  # `src/__init__.py`

# Prefixos das bibliotecas de I/O que o princípio 3 do doc 01 nomeia como
# proibidas em `domain` e `application`.
_IO_LIBS = ("httpx", "redis", "telegram", "langgraph", "langchain")

# Camadas que compõem a "aplicação pura" — o alvo do princípio 3.
_PURE_LAYERS = {_DOMAIN, _PORTS, _USE_CASES, _APPLICATION}


def _classify(module: str) -> str | None:
    """Camada de um módulo `src...`; `None` se for um top-level desconhecido."""
    if module == _ROOT_PACKAGE:
        return _ROOT
    if not module.startswith(_ROOT_PACKAGE + "."):
        return None
    rest = module[len(_ROOT_PACKAGE) + 1 :]
    parts = rest.split(".")
    head = parts[0]
    if head == "domain":
        return _DOMAIN
    if head == "application":
        if parts[1:2] == ["ports"]:
            return _PORTS
        if parts[1:2] == ["use_cases"]:
            return _USE_CASES
        return _APPLICATION
    if head == "infrastructure":
        return _INFRA
    if head == "interfaces":
        return _INTERFACES
    if rest == "container":
        return _CONTAINER
    if rest == "main":
        return _MAIN
    if rest == "settings":
        return _SETTINGS
    if rest == "logging_config":
        return _LOGGING
    return None


# Camadas internas que cada camada pode importar. `None` = livre.
#
# Desvio consciente do texto literal da tabela do doc 01: `infrastructure` também
# pode importar `application.use_cases` (adapters de entrada, como o
# `telegram/webhook_handler`, disparam use cases) e `settings` (a `llm/factory`
# lê a sua fatia de config). O que a tabela realmente protege — `infrastructure`
# nunca depende de `interfaces` nem da composition root — continua travado.
_ALLOWED_INTERNAL: dict[str, set[str] | None] = {
    _DOMAIN: {_DOMAIN},
    _PORTS: {_DOMAIN, _PORTS},
    _USE_CASES: {_DOMAIN, _PORTS, _USE_CASES},
    _APPLICATION: {_DOMAIN, _APPLICATION, _PORTS, _USE_CASES},
    _INFRA: {_DOMAIN, _APPLICATION, _PORTS, _USE_CASES, _INFRA, _SETTINGS, _LOGGING},
    _INTERFACES: {
        _APPLICATION, _PORTS, _USE_CASES, _INTERFACES, _CONTAINER, _MAIN, _SETTINGS, _LOGGING
    },
    _SETTINGS: {_SETTINGS, _DOMAIN},
    _LOGGING: {_LOGGING},
    _CONTAINER: None,
    _MAIN: None,
    _ROOT: None,
}

# Libs de terceiro que cada camada pode importar. `None` = qualquer uma;
# `frozenset()` = nenhuma (só stdlib).
_ALLOWED_THIRD_PARTY: dict[str, frozenset[str] | None] = {
    _DOMAIN: frozenset(),
    _PORTS: frozenset(),
    _USE_CASES: frozenset(),
    _APPLICATION: frozenset(),
    _INFRA: None,
    _INTERFACES: frozenset({"fastapi"}),
    _SETTINGS: frozenset({"pydantic", "pydantic_settings"}),
    _LOGGING: frozenset(),
    _CONTAINER: None,
    _MAIN: None,
    _ROOT: None,
}

# Camadas que `infrastructure` jamais pode alcançar.
_FORBIDDEN_FOR_INFRA = {_INTERFACES, _CONTAINER, _MAIN}


# --- varredura --------------------------------------------------------------


@dataclass(frozen=True)
class _Import:
    module: str
    lineno: int
    kind: str  # "stdlib" | "third_party" | "internal"
    layer: str | None  # camada-alvo quando kind == "internal"


@dataclass(frozen=True)
class _Module:
    name: str
    path: Path
    layer: str | None
    imports: tuple[_Import, ...]


def _top(module: str) -> str:
    return module.split(".", 1)[0]


def _module_name(path: Path) -> str:
    parts = list(path.relative_to(_SRC).with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join([_ROOT_PACKAGE, *parts]) if parts else _ROOT_PACKAGE


def _iter_imported(tree: ast.Module, module: str, is_pkg: bool) -> Iterator[tuple[str, int]]:
    """Módulos alvo de cada nó de import (inclui imports locais e sob `if`)."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name, node.lineno
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                if node.module:
                    yield node.module, node.lineno
                continue
            base = module.split(".")
            if not is_pkg:
                base = base[:-1]
            if node.level > 1:
                base = base[: -(node.level - 1)]
            prefix = ".".join(base)
            if node.module and prefix:
                yield f"{prefix}.{node.module}", node.lineno
            elif node.module or prefix:
                yield node.module or prefix, node.lineno


def _collect() -> list[_Module]:
    modules: list[_Module] = []
    for path in sorted(_SRC.rglob("*.py")):
        name = _module_name(path)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports: list[_Import] = []
        for imported, lineno in _iter_imported(tree, name, path.name == "__init__.py"):
            if imported == _ROOT_PACKAGE or imported.startswith(_ROOT_PACKAGE + "."):
                imports.append(_Import(imported, lineno, "internal", _classify(imported)))
            elif _top(imported) in sys.stdlib_module_names:
                imports.append(_Import(imported, lineno, "stdlib", None))
            else:
                imports.append(_Import(imported, lineno, "third_party", None))
        modules.append(_Module(name, path, _classify(name), tuple(imports)))
    return modules


_MODULES = _collect()
_CLASSIFIED = [m for m in _MODULES if m.layer is not None]


def _ids(mods: list[_Module]) -> list[str]:
    return [m.name for m in mods]


def _by_layer(*layers: str) -> list[_Module]:
    return [m for m in _CLASSIFIED if m.layer in layers]


# --- testes ----------------------------------------------------------------


def test_a_varredura_encontrou_os_modulos_do_projeto() -> None:
    nomes = {m.name for m in _MODULES}
    assert {"src.domain.entities", "src.container", "src.interfaces.http.app"} <= nomes
    assert len(_MODULES) > 20


@pytest.mark.parametrize("mod", _MODULES, ids=_ids(_MODULES))
def test_todo_modulo_de_src_pertence_a_uma_camada_conhecida(mod: _Module) -> None:
    assert mod.layer is not None, (
        f"{mod.name} ({mod.path.relative_to(_SRC.parent)}) não se encaixa em nenhuma "
        "camada conhecida; atualize `_classify` e a tabela de `docs/01-arquitetura.md`."
    )


@pytest.mark.parametrize("mod", _CLASSIFIED, ids=_ids(_CLASSIFIED))
def test_imports_internos_respeitam_a_tabela_de_camadas(mod: _Module) -> None:
    assert mod.layer is not None
    allowed = _ALLOWED_INTERNAL[mod.layer]
    if allowed is None:
        return
    offenders = [
        f"  L{imp.lineno}: {imp.module}  → camada `{imp.layer or '???'}`"
        for imp in mod.imports
        if imp.kind == "internal" and imp.layer not in allowed
    ]
    assert not offenders, (
        f"`{mod.name}` é da camada `{mod.layer}` e só pode importar de "
        f"{sorted(allowed)}.\nImports proibidos:\n" + "\n".join(offenders)
    )


@pytest.mark.parametrize("mod", _CLASSIFIED, ids=_ids(_CLASSIFIED))
def test_dependencias_externas_respeitam_a_camada(mod: _Module) -> None:
    assert mod.layer is not None
    allowed = _ALLOWED_THIRD_PARTY[mod.layer]
    if allowed is None:
        return
    offenders = [
        f"  L{imp.lineno}: {imp.module}"
        for imp in mod.imports
        if imp.kind == "third_party" and _top(imp.module) not in allowed
    ]
    permitido = sorted(allowed) if allowed else "(nenhuma — só stdlib)"
    assert not offenders, (
        f"`{mod.name}` (`{mod.layer}`) só pode usar as libs externas {permitido}.\n"
        "Imports proibidos:\n" + "\n".join(offenders)
    )


@pytest.mark.parametrize("mod", _by_layer(*_PURE_LAYERS), ids=_ids(_by_layer(*_PURE_LAYERS)))
def test_dominio_e_aplicacao_nao_conhecem_bibliotecas_de_io(mod: _Module) -> None:
    """Princípio 3 do doc 01: nada de `httpx`, `redis`, `telegram`, `langgraph`, `langchain*`."""
    offenders = [
        f"  L{imp.lineno}: {imp.module}"
        for imp in mod.imports
        if imp.kind == "third_party" and _top(imp.module).startswith(_IO_LIBS)
    ]
    assert not offenders, (
        f"`{mod.name}` está em `{mod.layer}` e importa biblioteca de I/O proibida "
        "pelo princípio 3 de `docs/01-arquitetura.md`:\n" + "\n".join(offenders)
    )


@pytest.mark.parametrize("mod", _by_layer(_INFRA), ids=_ids(_by_layer(_INFRA)))
def test_infrastructure_nao_importa_interfaces_nem_a_composition_root(mod: _Module) -> None:
    offenders = [
        f"  L{imp.lineno}: {imp.module}  → camada `{imp.layer}`"
        for imp in mod.imports
        if imp.kind == "internal" and imp.layer in _FORBIDDEN_FOR_INFRA
    ]
    assert not offenders, (
        f"`{mod.name}` é infraestrutura e não pode depender de `interfaces` nem da "
        "composition root (`container` / `main`):\n" + "\n".join(offenders)
    )
