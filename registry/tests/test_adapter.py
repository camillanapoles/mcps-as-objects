"""
Testes do adapter (bridge mcp-builder → mcps-as-objects).

Padrão:
  - Testar adapter.py DIRETAMENTE (sem MCP SDK, sem FastAPI)
  - Usar blueprint.yaml simulado em tmp_path
  - Parametrizado: 4 SDKs × 3 patterns + cenários de erro
  - Zero hardcoded: nenhum nome de MCP fixo
"""

import sys
import json
import os
from pathlib import Path

# Setup paths
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest
from adapter import ingest, info, sync

SDKS = ["python", "typescript", "go", "rust"]
PATTERNS = ["stateless", "event", "factory"]


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def blueprint_python_stateless(tmp_path):
    """Gera blueprint.yaml para Python stateless."""
    data = {
        "name": "test-python-stateless",
        "description": "Test MCP Python stateless",
        "sdk": "python",
        "pattern": "stateless",
        "tools": [
            {
                "name": "ping",
                "description": "Responde pong",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"}
                    },
                    "required": ["message"]
                },
                "outputSchema": {
                    "type": "object",
                    "properties": {
                        "result": {"type": "string"}
                    }
                }
            }
        ]
    }
    blueprint_path = tmp_path / "blueprint.yaml"
    import yaml
    with open(blueprint_path, "w") as f:
        yaml.dump(data, f)
    return tmp_path, data


@pytest.fixture
def blueprint_completo(tmp_path):
    """Blueprint completo com múltiplas tools e hooks."""
    data = {
        "name": "test-completo",
        "description": "MCP completo para teste",
        "sdk": "python",
        "pattern": "factory",
        "tools": [
            {
                "name": "analyze",
                "description": "Analisa dados",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "data": {"type": "string"}
                    },
                    "required": ["data"]
                },
                "outputSchema": {
                    "type": "object",
                    "properties": {
                        "result": {"type": "string"}
                    }
                }
            },
            {
                "name": "train",
                "description": "Treina modelo",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "epochs": {"type": "integer"}
                    },
                    "required": ["epochs"]
                },
                "outputSchema": {
                    "type": "object",
                    "properties": {
                        "accuracy": {"type": "number"}
                    }
                }
            }
        ],
        "hooks": {
            "gate": {"cost-limit": {}},
            "monitor": {"audit-log": {}}
        }
    }
    blueprint_path = tmp_path / "blueprint.yaml"
    import yaml
    with open(blueprint_path, "w") as f:
        yaml.dump(data, f)
    return tmp_path, data


# ── Testes de ingest ─────────────────────────────────────────────────

@pytest.mark.parametrize("sdk", SDKS)
@pytest.mark.parametrize("pattern", PATTERNS)
def test_ingest_sdk_pattern(sdk, pattern, tmp_path):
    """Ingest funciona com qualquer SDK + pattern."""
    import yaml
    data = {
        "name": f"test-{sdk}-{pattern}",
        "description": f"Test {sdk} {pattern}",
        "sdk": sdk,
        "pattern": pattern,
        "tools": [{
            "name": "ping",
            "description": "Responde pong",
            "inputSchema": {"type": "object", "properties": {}, "required": []},
            "outputSchema": {"type": "object", "properties": {"ok": {"type": "boolean"}}}
        }]
    }
    bp = tmp_path / "blueprint.yaml"
    yaml.dump(data, open(bp, "w"))

    result = ingest(str(tmp_path))
    assert result["ok"], f"Falhou para {sdk}/{pattern}: {result.get('error')}"
    assert sdk in result["mcp_id"]
    assert pattern in result["mcp_id"]
    assert result["action"] == "ingested"


def test_ingest_sem_blueprint(tmp_path):
    """Ingest sem blueprint.yaml tenta ler mcp.json."""
    # Cria mcp.json mínimo
    mcp_data = {
        "id": "test-sem-blueprint",
        "name": "Test Sem Blueprint",
        "version": "0.1.0",
        "entry": "src/server.py",
        "runtime": {"language": "python", "image": "ubuntu-22.04"},
        "functions": [{
            "name": "ping",
            "description": "ping pong",
            "input_schema": {"type": "object", "properties": {}},
            "output_schema": {"type": "object", "properties": {"ok": {"type": "boolean"}}}
        }],
        "platforms": ["*"]
    }
    mcp_path = tmp_path / "mcp.json"
    json.dump(mcp_data, open(mcp_path, "w"), indent=2)

    result = ingest(str(tmp_path))
    assert result["ok"], f"Falhou sem blueprint: {result.get('error')}"
    assert result["mcp_id"] == "test-sem-blueprint"


def test_ingest_projeto_inexistente():
    """Ingest de projeto que não existe retorna erro."""
    result = ingest("/caminho/inexistente")
    assert not result["ok"]
    assert "não encontrado" in result.get("error", "").lower()


def test_ingest_sem_blueprint_nem_mcpjson(tmp_path):
    """Ingest sem blueprint.yaml nem mcp.json retorna erro."""
    result = ingest(str(tmp_path))
    assert not result["ok"]
    assert "Nem blueprint.yaml nem mcp.json" in result.get("error", "")


def test_ingest_blueprint_completo(blueprint_completo):
    """Ingest de blueprint com múltiplas tools e hooks."""
    path, data = blueprint_completo
    result = ingest(str(path))
    assert result["ok"]
    assert result["mcp_id"] == "test-completo"
    assert result["from_blueprint"] is True


# ── Testes de info ───────────────────────────────────────────────────

def test_info_mcp_inexistente():
    """Info de MCP que não existe retorna erro."""
    result = info("mcp-inexistente-xyz")
    assert not result["ok"]
    assert "não encontrado" in result.get("error", "").lower()


# ── Testes de sync ──────────────────────────────────────────────────

def test_sync_mcp_inexistente():
    """Sync de MCP que não existe retorna erro."""
    result = sync("mcp-inexistente-xyz")
    assert not result["ok"]
    assert "não encontrado" in result.get("error", "").lower()


# ── Testes do blueprint gerado ──────────────────────────────────────

def test_blueprint_to_mcp_json_tem_campos_obrigatorios(blueprint_python_stateless):
    """O mcp.json gerado tem todos os campos obrigatórios do schema."""
    path, data = blueprint_python_stateless
    result = ingest(str(path))
    assert result["ok"]

    # Lê o mcp.json gerado
    from catalog import list_mcp_ids, read_manifest

    # Deve existir no catálogo
    ids = list_mcp_ids()
    mcp_id = result["mcp_id"]
    assert mcp_id in ids, f"{mcp_id} não encontrado no catálogo"

    man = read_manifest(mcp_id)
    assert man is not None
    assert man["id"] == mcp_id
    assert len(man["functions"]) == len(data["tools"])
    assert man["runtime"]["language"] == "python"
    assert "blueprint" in man
    assert man["blueprint"]["sdk"] == data["sdk"]
    assert man["blueprint"]["pattern"] == data["pattern"]


def test_server_py_gerado(blueprint_python_stateless):
    """server.py foi gerado e tem @mcp.tool()."""
    path, data = blueprint_python_stateless
    result = ingest(str(path))
    assert result["ok"]

    server_path = Path(__file__).resolve().parent.parent.parent / "mcps" / result["mcp_id"] / "src" / "server.py"
    assert server_path.exists()
    content = server_path.read_text()
    assert "@mcp.tool()" in content
    assert "FastMCP" in content
    assert data["tools"][0]["name"] in content or "ping" in content
