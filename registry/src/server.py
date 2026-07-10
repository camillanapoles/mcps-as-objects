#!/usr/bin/env python3
"""
MCP Server — expõe o registry como MCP (stdio transport).
Permite que o pi-coding-agent e outros clientes MCP consultem
e gerenciem o catálogo via protocolo MCP.
"""

import json
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

from . import db, crud, catalog, constructor, validator, snapshot

mcp = FastMCP(
    name="mcps-as-objects",
    description="Registry de MCPs determinístico — gestão, catálogo e composição.",
    version="0.1.0"
)


# ── Tools ──────────────────────────────────────────────────────────

@mcp.tool()
def list_mcps() -> list:
    """Lista todos os MCPs catalogados com id, name, version."""
    conn = db.get_conn()
    mcps = crud.list_mcps(conn)
    return [
        {"id": m["id"], "name": m["name"], "version": m["version"],
         "description": m.get("description", "")}
        for m in mcps
    ]


@mcp.tool()
def describe_mcp(mcp_id: str) -> dict:
    """
    Retorna o manifesto completo de um MCP.

    Args:
        mcp_id: ID do MCP (kebab-case).
    """
    man = catalog.read_manifest(mcp_id)
    if not man:
        return {"error": f"MCP '{mcp_id}' não encontrado"}
    return man


@mcp.tool()
def create_mcp(mcp_id: str, name: Optional[str] = None,
               description: Optional[str] = None, version: str = "0.1.0") -> dict:
    """
    Cria um novo MCP a partir do template determinístico.

    Args:
        mcp_id: ID do novo MCP (kebab-case, ex: 'meu-mcp').
        name: Nome amigável (opcional).
        description: Descrição (opcional).
        version: Versão semver (padrão 0.1.0).
    """
    try:
        dest = constructor.create_mcp(mcp_id, name, description, version)
        # Atualiza lockfile
        man = catalog.read_manifest(mcp_id)
        if man:
            catalog.update_lock(
                mcp_id=mcp_id,
                version=version,
                manifest_hash=catalog.manifest_hash(mcp_id) or ""
            )
        # Registra no DB
        conn = db.get_conn()
        crud.register_mcp(conn, mcp_id)
        return {"status": "created", "path": str(dest), "mcp_id": mcp_id}
    except (ValueError, FileExistsError) as exc:
        return {"status": "error", "message": str(exc)}


@mcp.tool()
def run_mcp_function(mcp_id: str, function_name: str, input_payload: dict) -> dict:
    """
    Executa uma função de um MCP.

    Args:
        mcp_id: ID do MCP.
        function_name: Nome da função.
        input_payload: Dict com argumentos.
    """
    # Usa a mesma lógica da API, mas via MCP tool
    # (em runtime local, executa inline)
    manifest = catalog.read_manifest(mcp_id)
    if not manifest:
        return {"error": f"MCP '{mcp_id}' não encontrado"}
    functions = [f for f in manifest.get("functions", []) if f["name"] == function_name]
    if not functions:
        return {"error": f"Função '{function_name}' não encontrada"}

    fn_def = functions[0]
    # Valida input contra schema (básico)
    inp_schema = fn_def.get("input_schema", {})
    required = inp_schema.get("required", [])
    for field in required:
        if field not in input_payload:
            return {"error": f"Campo obrigatório '{field}' não fornecido. Esperado: {required}"}

    # Tenta executar
    try:
        import importlib.util
        import sys
        server_path = catalog.ROOT / mcp_id / "src" / "server.py"
        if not server_path.exists():
            return {"error": f"Servidor não encontrado: {server_path}"}

        spec = importlib.util.spec_from_file_location(f"mcp_{mcp_id}", str(server_path))
        if not spec or not spec.loader:
            return {"error": "Falha ao carregar módulo do servidor"}
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        func = getattr(mod, function_name, None)
        if not func:
            return {"error": f"Função '{function_name}' não encontrada no servidor"}
        result = func(**input_payload)
        return {"status": "ok", "result": result}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@mcp.tool()
def validate_mcp(mcp_id: str) -> dict:
    """
    Valida o manifesto de um MCP contra os schemas.

    Args:
        mcp_id: ID do MCP.
    """
    man = catalog.read_manifest(mcp_id)
    if not man:
        return {"error": f"MCP '{mcp_id}' não encontrado"}
    valido, erros = validator.validate_manifest(man)
    return {"valid": valido, "errors": erros}


@mcp.tool()
def cache_key() -> str:
    """Retorna a chave de cache determinística para snapshot."""
    return snapshot.compute_cache_key()


@mcp.tool()
def pipeline_info() -> dict:
    """Retorna informações de pipeline (DAG de dependências)."""
    from .composer import build_graph_from_manifests
    mans = catalog.scan_catalog()
    graph = build_graph_from_manifests(mans)
    return {
        "nodes": list(graph.nodes.keys()),
        "execution_order": [f"{n.mcp_id}.{n.function_name}" for n in graph.execution_order()]
    }


if __name__ == "__main__":
    mcp.run()
