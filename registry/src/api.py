"""
REST API — FastAPI CRUD para o registry.
Endpoints para gestão de MCPs, consulta e execução.
Usada pelo workflow runtime e por consumidores externos (pi-coding).
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json

import db, crud, catalog, validator, snapshot
import platdetect as plat

app = FastAPI(
    title="MCPs as Objects — Registry API",
    version="0.1.0",
    description="API determinística de gestão de MCPs locais."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas Pydantic ──────────────────────────────────────────────

class MCPOut(BaseModel):
    id: str
    name: str
    version: str
    description: str
    manifest_hash: str
    registered_at: Optional[str] = None
    updated_at: Optional[str] = None

class FunctionOut(BaseModel):
    mcp_id: str
    name: str
    description: str
    input_schema: dict
    output_schema: dict

class RunCreate(BaseModel):
    mcp_id: str
    function_name: str
    input_payload: dict = {}
    workflow_run_id: str = ""

class RunOut(BaseModel):
    id: str
    mcp_id: str
    function_name: str
    input_payload: dict
    output_payload: Optional[dict] = None
    status: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None

class ManifestOut(BaseModel):
    id: str
    name: str
    version: str
    description: str
    entry: str
    runtime: dict
    functions: List[dict]
    permissions: list = []
    pipeline: dict = {}
    tags: list = []


# ── Dependency ────────────────────────────────────────────────────

def get_conn():
    """Retorna conexão SQLite."""
    return db.get_conn()


# ── Lifecycle ─────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    """Na inicialização, escaneia e registra todos os MCPs."""
    conn = get_conn()
    count = crud.scan_and_register_all(conn)
    print(f"[registry] {count} MCPs registrados no startup")


# ── Endpoints ─────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/mcps", response_model=List[MCPOut])
def list_mcps():
    conn = get_conn()
    return crud.list_mcps(conn)


@app.get("/mcps/{mcp_id}", response_model=MCPOut)
def get_mcp(mcp_id: str):
    conn = get_conn()
    mcp = crud.get_mcp(conn, mcp_id)
    if not mcp:
        raise HTTPException(404, f"MCP '{mcp_id}' não encontrado")
    return mcp


@app.get("/mcps/{mcp_id}/manifest", response_model=ManifestOut)
def get_manifest(mcp_id: str):
    """Retorna o manifesto completo do MCP."""
    man = catalog.read_manifest(mcp_id)
    if not man:
        raise HTTPException(404, f"Manifesto '{mcp_id}' não encontrado")
    return man


@app.get("/mcps/{mcp_id}/functions", response_model=List[FunctionOut])
def list_functions(mcp_id: str):
    conn = get_conn()
    return crud.list_functions(conn, mcp_id)


@app.delete("/mcps/{mcp_id}", status_code=204)
def delete_mcp(mcp_id: str):
    conn = get_conn()
    if not crud.delete_mcp(conn, mcp_id):
        raise HTTPException(404, f"MCP '{mcp_id}' não encontrado")


@app.post("/mcps/{mcp_id}/run", response_model=RunOut)
def run_mcp_function(mcp_id: str, body: RunCreate):
    """
    Executa uma função de um MCP.
    Em runtime local, executa inline. Em GitHub Actions, o workflow
    coordena a execução e depois reporta o resultado via PATCH.
    """
    conn = get_conn()
    manifest = catalog.read_manifest(mcp_id)
    if not manifest:
        raise HTTPException(404, f"MCP '{mcp_id}' não encontrado")

    # Valida função
    functions = [f for f in manifest.get("functions", []) if f["name"] == body.function_name]
    if not functions:
        raise HTTPException(400, f"Função '{body.function_name}' não encontrada em '{mcp_id}'")

    # Cria run
    run_id = crud.create_run(conn, mcp_id, body.function_name, body.input_payload, body.workflow_run_id)

    # Tenta executar inline (para dev/local)
    try:
        import importlib
        import sys
        from pathlib import Path
        server_path = Path(MCPS_DIR := catalog.ROOT / mcp_id) / "src" / "server.py"
        if server_path.exists():
            # Carrega o módulo dinamicamente
            spec = importlib.util.spec_from_file_location(f"mcp_{mcp_id}", str(server_path))
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = mod
                spec.loader.exec_module(mod)
                func = getattr(mod, body.function_name, None)
                if func:
                    result = func(**body.input_payload)
                    crud.finish_run(conn, run_id, result, "ok")
                    run = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
                    return dict(run) if run else {"id": run_id, "status": "ok"}
    except Exception as exc:
        crud.finish_run(conn, run_id, {"error": str(exc)}, "error")
        run = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        if run:
            return dict(run)

    run = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    return dict(run) if run else {"id": run_id, "status": "pending"}


@app.post("/mcps/{mcp_id}/validate")
def validate_mcp(mcp_id: str):
    """Valida o manifesto de um MCP contra os schemas."""
    man = catalog.read_manifest(mcp_id)
    if not man:
        raise HTTPException(404, f"MCP '{mcp_id}' não encontrado")
    valido, erros = validator.validate_manifest(man)
    return {"id": mcp_id, "valid": valido, "errors": erros}


@app.post("/registry/scan")
def scan_registry():
    """Escaneia o filesystem e registra todos os MCPs."""
    conn = get_conn()
    count = crud.scan_and_register_all(conn)
    return {"registered": count}


@app.get("/snapshot/key")
def snapshot_key():
    """Retorna a chave de cache determinística atual."""
    key = snapshot.compute_cache_key()
    return {"cache_key": key, "algorithm": "sha256(mcps-lock.json)+sha256(uname)"}


@app.get("/pipeline/graph")
def pipeline_graph():
    """Retorna o grafo de pipeline (DAG de dependências)."""
    from composer import build_graph_from_manifests
    mans = catalog.scan_catalog()
    graph = build_graph_from_manifests(mans)
    return {
        "nodes": list(graph.nodes.keys()),
        "order": [f"{n.mcp_id}.{n.function_name}" for n in graph.execution_order()]
    }


@app.get("/platform")
def platform_info():
    """Retorna info da plataforma atual."""
    current = plat.detect_platform()
    all_plats = plat.detect_platforms()
    return {
        "platform": current,
        "label": plat.platform_label(current),
        "all_applicable": all_plats
    }


@app.get("/mcps/compatible")
def list_compatible_mcps():
    """Lista apenas MCPs compatíveis com a plataforma atual."""
    from catalog import scan_catalog_filtered
    return scan_catalog_filtered(platform_filter=True)


@app.get("/mcps/{mcp_id}/compatibility")
def check_mcp_compatibility(mcp_id: str):
    """Verifica se um MCP específico é compatível com a plataforma atual."""
    man = catalog.read_manifest(mcp_id)
    if not man:
        raise HTTPException(404, f"MCP '{mcp_id}' não encontrado")
    compatible, reason = plat.mcp_is_compatible(man)
    return {
        "mcp_id": mcp_id,
        "platform": plat.detect_platform(),
        "compatible": compatible,
        "reason": reason,
        "mcp_platforms": man.get("platforms", ["*"])
    }


@app.post("/mcps/{mcp_id}/dispatch", status_code=202)
def dispatch_mcp(mcp_id: str, background_tasks: BackgroundTasks):
    """
    Dispara execução de UM MCP específico via GitHub Actions (event-driven).
    Retorna 202 Accepted com o run_id do workflow.
    """
    import subprocess
    import json

    man = catalog.read_manifest(mcp_id)
    if not man:
        raise HTTPException(404, f"MCP '{mcp_id}' não encontrado")

    # Verifica compatibilidade
    compatible, reason = plat.mcp_is_compatible(man)
    if not compatible:
        raise HTTPException(400, f"MCP '{mcp_id}' incompatível: {reason}")

    # Dispara workflow via gh CLI
    try:
        result = subprocess.run(
            ["gh", "workflow", "run", "mcp-runtime.yml",
             "--repo", "camillanapoles/mcps-as-objects",
             "-f", f"mcp_id={mcp_id}"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            run_url = result.stdout.strip()
            run_id = run_url.split("/")[-1] if run_url else ""
            return {
                "status": "dispatched",
                "mcp_id": mcp_id,
                "run_id": run_id,
                "run_url": run_url,
                "message": f"🚀 {mcp_id} disparado como workflow event"
            }
        else:
            raise HTTPException(502, f"Falha ao disparar workflow: {result.stderr}")
    except FileNotFoundError:
        raise HTTPException(502, "gh CLI não disponível neste ambiente")
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "Timeout ao disparar workflow")
