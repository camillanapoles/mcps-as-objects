"""
Teste de fumaça para o MCP template.
Valida que o server pode ser importado e as ferramentas estão registradas.
"""

import json
import sys
from pathlib import Path

# Adiciona src/ ao path para import
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from server import mcp


def test_server_imports():
    """O servidor MCP pode ser importado e tem as ferramentas esperadas."""
    assert mcp is not None
    assert hasattr(mcp, "_tool_manager")
    tools = mcp._tool_manager.list_tools()
    tool_names = [t.name for t in tools]
    assert "exemplo" in tool_names, f"Ferramenta 'exemplo' não encontrada. Tem: {tool_names}"


def test_tool_exemplo_schema():
    """A ferramenta exemplo tem os parâmetros esperados."""
    tools = mcp._tool_manager.list_tools()
    exemplo_tool = next(t for t in tools if t.name == "exemplo")
    assert exemplo_tool.description, "Tool precisa ter descrição"

    # Verifica os parâmetros via inputSchema
    schema = exemplo_tool.inputSchema
    assert "message" in schema.get("properties", {}), \
        f"Faltando parâmetro 'message'. Propriedades: {schema.get('properties', {})}"
    assert schema["properties"]["message"]["type"] == "string"
    assert "message" in schema.get("required", []), "'message' deve ser required"
