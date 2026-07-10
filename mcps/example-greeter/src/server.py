"""
Example Greeter — MCP de demonstração do padrão mcps-as-objects.
Expõe funções greet (saudação) e sum (soma).
"""

from datetime import datetime, timezone
from typing import Optional
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="example-greeter",
    version="0.1.0"
)

SAUDS = {
    "pt": "Olá",
    "en": "Hello",
    "es": "Hola",
}


@mcp.tool()
def greet(name: str, lang: Optional[str] = "pt") -> dict:
    """
    Gera uma saudação personalizada.

    Args:
        name: Nome da pessoa.
        lang: Idioma (pt, en, es). Padrão: pt.

    Returns:
        dict: Saudação formatada.
    """
    saud = SAUDS.get(lang, SAUDS["pt"])
    greeting = f"{saud}, {name}!"
    return {
        "greeting": greeting,
        "lang": lang or "pt",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@mcp.tool()
def sum(a: float, b: float) -> dict:
    """
    Soma dois números.

    Args:
        a: Primeiro número.
        b: Segundo número.

    Returns:
        dict: Resultado da soma.
    """
    return {
        "result": a + b,
        "operation": f"{a} + {b} = {a + b}"
    }


if __name__ == "__main__":
    mcp.run()
