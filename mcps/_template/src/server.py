"""
Template MCP Server — Siga este padrão para criar novos MCPs.

Regras:
  • O arquivo DEVE se chamar `server.py` e ficar em `src/`.
  • Use `FastMCP` (MCP SDK Python).
  • Adicione ferramentas com `@mcp.tool()` usando nomes snake_case.
  • Cada função DEVE ter input_schema e output_schema correspondentes no mcp.json.
  • Evite estado global. Se precisar, use injeção de contexto.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="{{ MCP_NAME }}",
    description="{{ MCP_DESCRIPTION }}",
    version="{{ MCP_VERSION }}"
)


@mcp.tool()
def exemplo(message: str) -> dict:
    """
    {{ MCP_EXEMPLO_DESCRIPTION }}

    Args:
        message: Mensagem de entrada.

    Returns:
        dict: Objeto com echo e timestamp.
    """
    from datetime import datetime, timezone
    return {
        "echo": message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


if __name__ == "__main__":
    mcp.run()
