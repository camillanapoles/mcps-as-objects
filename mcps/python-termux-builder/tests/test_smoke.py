"""
Testes de fumaça para python-termux-builder.
Valida a lógica de detecção de compatibilidade offline (sem PyPI).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core import (
    check_package,
    check_requirements,
    list_cached_wheels,
    PURE_PYTHON,
    NEEDS_EXTERNAL_BUILD,
    build_wheel,
)


def test_check_package_pure_python():
    """check_package identifica pacotes pure-Python corretamente."""
    result = check_package("click")
    assert result["compatible"] is True
    assert result["type"] == "pure-python"
    assert result["needs_external_build"] is False


def test_check_package_rust_ext():
    """check_package identifica pacotes com extensão Rust."""
    result = check_package("rpds-py")
    assert result["compatible"] is False
    assert result["type"] == "rust-ext"
    assert result["needs_external_build"] is True
    assert "Rust" in result["reason"]


def test_check_package_c_ext():
    """check_package identifica pacotes com extensão C."""
    result = check_package("cryptography")
    assert result["compatible"] is False
    assert result["type"] == "c-ext"
    assert result["needs_external_build"] is True


def test_check_package_unknown():
    """Pacote não catalogado retorna type=unknown com compatible=True (fallback seguro)."""
    result = check_package("pacote-ficticio-xyz-123")
    assert result["compatible"] is True
    # Sem consulta PyPI = unknown
    assert result["type"] in ("pure-python", "unknown")


def test_check_package_case_insensitive():
    """Nomes em maiúsculo são normalizados."""
    result = check_package("RustPACKAGEany")
    assert result["compatible"] is True  # Fallback seguro


def test_check_requirements_all_pure():
    """requirements com só pure-python."""
    result = check_requirements("click\nrich\npydantic")
    assert result["total_packages"] == 3
    assert len(result["needs_build"]) == 0
    assert "todos" in result["summary"].lower()


def test_check_requirements_mixed():
    """requirements misto: pure + c-ext."""
    result = check_requirements("click\nrpds-py\ncryptography\nfastapi")
    assert result["total_packages"] == 4
    assert "rpds-py" in result["needs_build"]
    assert "cryptography" in result["needs_build"]
    assert "click" in result["compatible"]
    assert "fastapi" in result["compatible"]


def test_check_requirements_with_versions():
    """Linhas com versões são parseadas corretamente."""
    result = check_requirements("requests>=2.28\npydantic<2.0\nclick>=8.0,<9.0")
    assert "requests" in result["compatible"]
    assert "pydantic" in result["compatible"]
    assert "click" in result["compatible"]


def test_check_requirements_empty():
    """requirements vazio."""
    result = check_requirements("")
    assert result["total_packages"] == 0


def test_check_requirements_comments():
    """Comentários e linhas em branco ignorados."""
    result = check_requirements("# comentário\n  \n--index-url https://x.com\nclick")
    assert result["total_packages"] == 1
    assert "click" in result["compatible"]


def test_list_cached_wheels_empty():
    """Lista wheels vazia inicialmente."""
    result = list_cached_wheels()
    assert result["total"] == 0
    assert result["wheels"] == []


def test_list_cached_wheels_filter():
    """Filtrar com nome não existente."""
    result = list_cached_wheels(package_name="inexistente")
    assert result["total"] == 0


def test_known_packages_exist():
    """As listas de pacotes conhecidos não estão vazias."""
    assert len(PURE_PYTHON) > 10, "PURE_PYTHON muito pequeno"
    assert len(NEEDS_EXTERNAL_BUILD) > 5, "NEEDS_EXTERNAL_BUILD muito pequeno"


def test_build_wheel_no_gh():
    """build_wheel sem gh CLI retorna instruções manuais."""
    result = build_wheel("rpds-py")
    assert result["success"] is False
    assert "manual" in result["action"] or "gh" in result.get("error", "")


def test_pipeline_produces():
    """O manifesto declara as 4 ferramentas como produced."""
    import json
    man_path = Path(__file__).parent.parent / "mcp.json"
    man = json.loads(man_path.read_text())
    produced = man.get("pipeline", {}).get("produces", [])
    assert len(produced) == 4
    assert all(p.startswith("python-termux-builder.") for p in produced)
