"""
Testes de fumaça para example-greeter.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from server import mcp, SAUDS


def test_server_has_tools():
    """As ferramentas esperadas estão registradas."""
    tools = mcp._tool_manager.list_tools()
    names = [t.name for t in tools]
    assert "greet" in names, f"Falta 'greet'. Tem: {names}"
    assert "sum" in names, f"Falta 'sum'. Tem: {names}"
    assert len(tools) == 2


def test_greet_input_schema():
    """greet aceita name (obrigatório) e lang (opcional)."""
    tools = mcp._tool_manager.list_tools()
    greet_tool = next(t for t in tools if t.name == "greet")
    schema = greet_tool.inputSchema
    props = schema.get("properties", {})
    assert "name" in props
    assert props["name"]["type"] == "string"
    assert "name" in schema.get("required", [])


def test_sum_input_schema():
    """sum aceita a e b (números, obrigatórios)."""
    tools = mcp._tool_manager.list_tools()
    sum_tool = next(t for t in tools if t.name == "sum")
    schema = sum_tool.inputSchema
    props = schema.get("properties", {})
    assert "a" in props and "b" in props
    assert "a" in schema.get("required", [])
    assert "b" in schema.get("required", [])


def test_greet_logic():
    """greet produz saudação correta."""
    import server
    # Invoca direto (não via MCP transport)
    result = server.greet(name="João", lang="pt")
    assert result["greeting"] == "Olá, João!"
    assert result["lang"] == "pt"

    result_en = server.greet(name="John", lang="en")
    assert result_en["greeting"] == "Hello, John!"
    assert result_en["lang"] == "en"

    result_es = server.greet(name="Juan", lang="es")
    assert result_es["greeting"] == "Hola, Juan!"
    assert result_es["lang"] == "es"


def test_sum_logic():
    """sum produz resultado correto."""
    import server
    result = server.sum(a=3, b=5)
    assert result["result"] == 8
    assert "3 + 5 = 8" in result["operation"]

    result_neg = server.sum(a=-1, b=1)
    assert result_neg["result"] == 0
