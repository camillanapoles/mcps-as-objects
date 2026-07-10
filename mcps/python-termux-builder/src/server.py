"""
Python Termux Builder — MCP Server (thin wrapper).
A lógica está em core.py; este arquivo apenas expõe as funções via FastMCP.
"""

from mcp.server.fastmcp import FastMCP
from core import check_package as _check_package
from core import build_wheel as _build_wheel
from core import list_cached_wheels as _list_cached_wheels
from core import check_requirements as _check_requirements

mcp = FastMCP(
    name="python-termux-builder",
    version="0.1.0"
)


@mcp.tool()
def check_package(package_name: str, python_version: str = "3.12") -> dict:
    """
    Verifica se um pacote Python pode ser instalado em Termux.

    Args:
        package_name: Nome do pacote PyPI.
        python_version: Versão do Python (3.11, 3.12, 3.13).

    Returns:
        dict: Diagnóstico de compatibilidade.
    """
    return _check_package(package_name, python_version)


@mcp.tool()
def build_wheel(package_name: str, package_version: str = "",
                python_version: str = "3.12") -> dict:
    """
    Dispara build externo de wheel aarch64 via GitHub Actions.

    Args:
        package_name: Nome do pacote PyPI.
        package_version: Versão específica (vazio = latest).
        python_version: Versão Python alvo.

    Returns:
        dict: Status do build incluindo run_id.
    """
    return _build_wheel(package_name, package_version, python_version)


@mcp.tool()
def list_cached_wheels(package_name: str = "") -> dict:
    """
    Lista wheels Android disponíveis no cache local.

    Args:
        package_name: Filtrar por nome (vazio = todos).

    Returns:
        dict: Lista de wheels e total.
    """
    return _list_cached_wheels(package_name)


@mcp.tool()
def check_requirements(requirements_text: str) -> dict:
    """
    Analisa um requirements.txt e reporta compatibilidade Termux.

    Args:
        requirements_text: Conteúdo do requirements.txt (multiline).

    Returns:
        dict: Pacotes compatíveis, os que precisam build, summary.
    """
    return _check_requirements(requirements_text)


if __name__ == "__main__":
    mcp.run()
