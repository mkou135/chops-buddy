"""Tests for docs/ENGINE_SPEC.md E-01, E-02: the engine package is pure."""

import ast
import sys
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parents[2] / "src" / "chops_buddy" / "engine"
ALLOWED_TOP_LEVEL = {"pydantic", "chops_buddy.engine"}
FORBIDDEN_MODULES = {
    "random",
    "time",
    "datetime",
    "os",
    "io",
    "pathlib",
    "socket",
    "uuid",
    "secrets",
}


def _imports() -> list[tuple[Path, str]]:
    found: list[tuple[Path, str]] = []
    for py in ENGINE_DIR.glob("*.py"):
        tree = ast.parse(py.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.extend((py, alias.name) for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                found.append((py, node.module))
    return found


def _is_stdlib(module: str) -> bool:
    return module.split(".")[0] in sys.stdlib_module_names


def test_engine_imports_only_stdlib_and_pydantic() -> None:
    offenders = [
        (py.name, mod)
        for py, mod in _imports()
        if not (
            _is_stdlib(mod) or any(mod == a or mod.startswith(a + ".") for a in ALLOWED_TOP_LEVEL)
        )
    ]
    assert offenders == []


def test_engine_has_no_io_clock_or_random() -> None:
    offenders = [(py.name, mod) for py, mod in _imports() if mod.split(".")[0] in FORBIDDEN_MODULES]
    assert offenders == []
    source = "".join(py.read_text() for py in ENGINE_DIR.glob("*.py"))
    for token in ("open(", "print(", "input("):
        assert token not in source
