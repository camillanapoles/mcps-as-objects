"""
adapter.py — Bridge entre mcp-builder (blueprint.yaml) e mcps-as-objects (mcp.json).

Zero hardcoded: tudo lido de blueprint.yaml + schemas.
Agnóstico: funciona com Python, TS, Go, Rust — qualquer SDK/pattern.
Gerenciado: registra no DB, lockfile, verify.
Determinístico: mesmo blueprint → mesmo mcp.json → mesmo hash.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime, timezone

# ── Imports do registry ──────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent))
import db
import crud
import catalog
import validator
import verifier


# ── Constantes ───────────────────────────────────────────────────────

MCPS_DIR = Path(__file__).resolve().parent.parent.parent / "mcps"
SCHEMAS_DIR = Path(__file__).resolve().parent.parent.parent / "schemas"

SDK_MAP = {
    "python": "python",
    "typescript": "node",
    "go": "go",
    "rust": "rust",
}

PATTERN_MAP = {
    "stateless": "stateless",
    "event": "event",
    "factory": "factory",
}

VALID_PLATFORMS = {"*", "linux/amd64", "linux/arm64", "android/termux",
                   "darwin/amd64", "darwin/arm64"}


# ── Core ─────────────────────────────────────────────────────────────

def ingest(
    project_path: str,
    platforms: Optional[List[str]] = None,
    overwrite: bool = False,
) -> dict:
    """
    Ingere um projeto gerado pelo mcp-builder no ecossistema mcps-as-objects.

    Fluxo:
    1. Lê blueprint.yaml (se existir) ou mcp.json
    2. Extrai: id, name, tools → functions, sdk, pattern, hooks
    3. Cria mcps/<id>/ com mcp.json + server.py
    4. Valida contra schema
    5. Executa verify-mcp (15 checks)
    6. Atualiza lockfile (SHA-256)
    7. Registra no SQLite

    Args:
        project_path: Caminho do projeto gerado pelo mcp-builder.
        platforms: Lista de plataformas (ex: ["*"], ["android/termux"]).
        overwrite: Se True, sobrescreve MCP existente.

    Returns:
        dict: {ok, mcp_id, manifest_hash, action, error?}
    """
    proj = Path(project_path)
    platforms = platforms or ["*"]

    if not proj.exists():
        return {"ok": False, "error": f"Projeto não encontrado: {project_path}"}

    # 1. Ler blueprint.yaml ou mcp.json
    blueprint_path = proj / "blueprint.yaml"
    manifest_path = proj / "mcp.json"

    if blueprint_path.exists():
        try:
            import yaml as _yaml
            blueprint = _yaml.safe_load(blueprint_path.read_text())
        except ImportError:
            return {"ok": False, "error": "PyYAML necessário para ler blueprint.yaml"}
        except Exception as e:
            return {"ok": False, "error": f"Erro ao ler blueprint.yaml: {e}"}
    else:
        blueprint = {}

    # 2. Extrair metadados
    mcp_id = _extract_id(blueprint, manifest_path)
    if not mcp_id:
        return {"ok": False, "error": "Não foi possível extrair mcp_id do projeto"}

    # 3. Gerar mcp.json
    mcp_dir = MCPS_DIR / mcp_id

    # Se não existe mcp.json, gerar a partir do blueprint
    if not manifest_path.exists() and blueprint:
        mcp_json = _blueprint_to_mcp_json(blueprint, mcp_id, platforms)
        mcp_dir.mkdir(parents=True, exist_ok=True)
        (mcp_dir / "mcp.json").write_text(
            json.dumps(mcp_json, indent=2, ensure_ascii=False) + "\n"
        )
        manifest_path = mcp_dir / "mcp.json"

        # Gerar server.py (FastMCP wrapper)
        server_py = _generate_server_py(blueprint, mcp_id)
        src_dir = mcp_dir / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        (src_dir / "server.py").write_text(server_py)

        # Copiar tests se existirem
        tests_src = proj / "tests"
        if tests_src.exists():
            import shutil
            tests_dst = mcp_dir / "tests"
            if tests_dst.exists():
                shutil.rmtree(tests_dst)
            shutil.copytree(tests_src, tests_dst)
    elif manifest_path.exists():
        # Copiar mcp.json existente para mcps/<id>/
        data = json.loads(manifest_path.read_text())
        mcp_dir.mkdir(parents=True, exist_ok=True)
        (mcp_dir / "mcp.json").write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        )
        # Copiar src/ se existir
        src_src = proj / "src"
        if src_src.exists():
            import shutil
            src_dst = mcp_dir / "src"
            if src_dst.exists():
                shutil.rmtree(src_dst)
            shutil.copytree(src_src, src_dst)
        # Copiar tests se existirem
        tests_src = proj / "tests"
        if tests_src.exists():
            import shutil
            tests_dst = mcp_dir / "tests"
            if tests_dst.exists():
                shutil.rmtree(tests_dst)
            shutil.copytree(tests_src, tests_dst)
    else:
        return {"ok": False, "error": "Nem blueprint.yaml nem mcp.json encontrados"}

    # 4. Validar contra schema
    if manifest_path.exists():
        valido, erros = validator.validate_manifest_file(str(manifest_path))
        if not valido:
            return {"ok": False, "error": f"Manifesto inválido contra schema: {erros}"}

    # 5. Verify-mcp (15 checks)
    try:
        ok, msg = verifier.verify_new_mcp(mcp_id)
        if not ok:
            return {"ok": False, "error": f"verify-mcp falhou: {msg}"}
    except Exception as e:
        return {"ok": False, "error": f"verify-mcp exception: {e}"}

    # 6. Lockfile
    mhash = catalog.manifest_hash(mcp_id)
    man = catalog.read_manifest(mcp_id)
    if man and mhash:
        catalog.update_lock(mcp_id, man.get("version", "0.1.0"), mhash)

    # 7. Registrar no DB
    conn = db.get_conn()
    crud.register_mcp(conn, mcp_id)
    conn.close()

    return {
        "ok": True,
        "mcp_id": mcp_id,
        "manifest_hash": mhash,
        "action": "ingested",
        "from_blueprint": blueprint_path.exists(),
    }


def info(mcp_id: str) -> dict:
    """
    Retorna info consolidada de um MCP gerenciado.

    Returns: manifesto, blueprint, FSM, hooks, runs recentes, cache key.
    """
    mcp_dir = MCPS_DIR / mcp_id
    if not mcp_dir.exists():
        return {"ok": False, "error": f"MCP '{mcp_id}' não encontrado em {mcp_dir}"}

    result = {"ok": True, "mcp_id": mcp_id}

    # Manifesto
    man = catalog.read_manifest(mcp_id)
    if man:
        result["manifest"] = {
            "id": man["id"],
            "name": man.get("name"),
            "version": man.get("version"),
            "description": man.get("description", ""),
            "functions": [f["name"] for f in man.get("functions", [])],
            "platforms": man.get("platforms", ["*"]),
        }

    # Blueprint
    blueprint_path = mcp_dir / "blueprint.yaml"
    if blueprint_path.exists():
        try:
            import yaml as _yaml
            result["blueprint"] = _yaml.safe_load(blueprint_path.read_text())
        except Exception:
            result["blueprint"] = {"error": "Erro ao ler blueprint.yaml"}

    # FSM
    fsm_states = mcp_dir / ".mcp" / "state" / "states.yaml"
    fsm_transitions = mcp_dir / ".mcp" / "state" / "transitions.yaml"
    if fsm_states.exists() and fsm_transitions.exists():
        try:
            import yaml as _yaml
            result["fsm"] = {
                "states": _yaml.safe_load(fsm_states.read_text()),
                "transitions": _yaml.safe_load(fsm_transitions.read_text()),
            }
        except Exception:
            result["fsm"] = {"error": "Erro ao ler FSM"}

    # Runs recentes
    conn = db.get_conn()
    rows = conn.execute(
        "SELECT id, function_name, status, started_at, finished_at "
        "FROM runs WHERE mcp_id = ? ORDER BY started_at DESC LIMIT 5",
        (mcp_id,),
    ).fetchall()
    conn.close()
    result["recent_runs"] = [dict(r) for r in rows]

    # Cache key
    from snapshot import compute_cache_key
    result["cache_key"] = compute_cache_key()

    # Hooks (do blueprint)
    if "blueprint" in result and isinstance(result["blueprint"], dict):
        hooks = result["blueprint"].get("hooks", {})
        result["hooks"] = {
            cat: list(hk.keys()) if isinstance(hk, dict) else hk
            for cat, hk in hooks.items()
        }

    return result


def sync(mcp_id: str) -> dict:
    """
    Sincroniza MCP com o filesystem.
    Se blueprint ou código mudou, revalida, religa, re-registra.

    Returns: {ok, mcp_id, action, changes?}
    """
    mcp_dir = MCPS_DIR / mcp_id
    if not mcp_dir.exists():
        return {"ok": False, "error": f"MCP '{mcp_id}' não encontrado"}

    # Verificar se houve mudança (comparar hash atual com lockfile)
    current_hash = catalog.manifest_hash(mcp_id)
    lock = catalog.read_lockfile()
    locked_hash = lock.get("entries", {}).get(mcp_id, {}).get("manifest_hash", "")

    if current_hash == locked_hash:
        return {
            "ok": True,
            "mcp_id": mcp_id,
            "action": "noop",
            "message": "Nenhuma mudança detectada",
        }

    # Revalidar
    valido, erros = validator.validate_manifest_file(str(mcp_dir / "mcp.json"))
    if not valido:
        return {
            "ok": False,
            "mcp_id": mcp_id,
            "action": "validation_failed",
            "error": erros,
        }

    # Re-verify
    try:
        ok, msg = verifier.verify_new_mcp(mcp_id)
        if not ok:
            return {"ok": False, "mcp_id": mcp_id, "action": "verify_failed", "error": msg}
    except Exception as e:
        return {"ok": False, "mcp_id": mcp_id, "action": "verify_error", "error": str(e)}

    # Relock
    man = catalog.read_manifest(mcp_id)
    if man and current_hash:
        catalog.update_lock(mcp_id, man.get("version", "0.1.0"), current_hash)

    # Re-registrar
    conn = db.get_conn()
    crud.register_mcp(conn, mcp_id)
    conn.close()

    return {
        "ok": True,
        "mcp_id": mcp_id,
        "action": "synced",
        "manifest_hash": current_hash,
        "message": "MCP revalidado e lockfile atualizado",
    }


# ── Helpers ──────────────────────────────────────────────────────────


def _extract_id(blueprint: dict, manifest_path: Path) -> Optional[str]:
    """Extrai mcp_id do blueprint ou manifesto."""
    # Tenta do blueprint
    name = blueprint.get("name", "")
    if name:
        # Converte para kebab-case
        mcp_id = name.lower().strip().replace(" ", "-")
        mcp_id = re.sub(r"[^a-z0-9-]", "", mcp_id)
        mcp_id = re.sub(r"-+", "-", mcp_id).strip("-")
        if mcp_id:
            return mcp_id

    # Tenta do manifesto
    if manifest_path.exists():
        try:
            return json.loads(manifest_path.read_text()).get("id")
        except Exception:
            pass

    return None


def _blueprint_to_mcp_json(
    blueprint: dict, mcp_id: str, platforms: Optional[List[str]] = None
) -> dict:
    """Converte blueprint.yaml em mcp.json compatível com mcps-as-objects."""
    platforms = platforms or ["*"]
    sdk = blueprint.get("sdk", "python")
    pattern = blueprint.get("pattern", "stateless")
    tools = blueprint.get("tools", [])

    functions = []
    for tool in tools:
        name = tool.get("name", "tool")
        # Converte camelCase/kebab para snake_case
        name_snake = re.sub(r"([a-z])([A-Z])", r"\1_\2", name)
        name_snake = name_snake.lower().replace("-", "_")

        functions.append({
            "name": name_snake,
            "description": tool.get("description", ""),
            "input_schema": tool.get("inputSchema", {"type": "object", "properties": {}, "required": []}),
            "output_schema": tool.get("outputSchema", {"type": "object", "properties": {}, "required": []}),
        })

    mcp_json = {
        "id": mcp_id,
        "name": blueprint.get("name", mcp_id),
        "version": "0.1.0",
        "description": blueprint.get("description", f"MCP {mcp_id} gerado pelo mcp-builder"),
        "entry": "src/server.py",
        "runtime": {
            "language": SDK_MAP.get(sdk, "python"),
            "image": "ubuntu-22.04",
            "estimated_duration_sec": 60,
            "dependencies": {
                SDK_MAP.get(sdk, "python"): "requirements.txt"
            } if sdk == "python" else {}
        },
        "functions": functions,
        "permissions": [],
        "pipeline": {
            "consumes": [],
            "produces": [f"{mcp_id}.{f['name']}" for f in functions]
        },
        "platforms": [p for p in platforms if p in VALID_PLATFORMS] or ["*"],
        "tags": [sdk, pattern],
        "blueprint": {
            "sdk": sdk,
            "pattern": pattern,
            "hooks": blueprint.get("hooks", {}),
        },
    }

    return mcp_json


def _generate_server_py(blueprint: dict, mcp_id: str) -> str:
    """Gera server.py (FastMCP wrapper) a partir do blueprint."""
    sdk = blueprint.get("sdk", "python")
    tools = blueprint.get("tools", [])
    name = blueprint.get("name", mcp_id)
    description = blueprint.get("description", "")

    if sdk != "python":
        return f"""# {mcp_id} — MCP server gerado pelo mcp-builder
# SDK: {sdk}
# ATENÇÃO: FastMCP wrapper só gerado para Python.
# Para {sdk}, use o server gerado pelo template nativo.
"""

    # Gera funções
    func_defs = []
    tool_decorators = []
    for i, tool in enumerate(tools):
        tool_name = tool.get("name", f"tool_{i}")
        # snake_case
        name_snake = re.sub(r"([a-z])([A-Z])", r"\1_\2", tool_name)
        name_snake = name_snake.lower().replace("-", "_")
        desc = tool.get("description", "")
        input_schema = tool.get("inputSchema", {})
        props = input_schema.get("properties", {})

        # Parâmetros da função
        params = []
        for pname, pdef in props.items():
            ptype = pdef.get("type", "str")
            py_type = {"string": "str", "number": "float", "integer": "int",
                       "boolean": "bool", "object": "dict", "array": "list"}.get(ptype, "str")
            default = pdef.get("default")
            if default is not None:
                params.append(f"{pname}: {py_type} = {json.dumps(default)}")
            else:
                params.append(f"{pname}: {py_type}")

        params_str = ", ".join(params)
        func_defs.append(f"""
@mcp.tool()
def {name_snake}({params_str}) -> dict:
    \"\"\"{desc}\"\"\"
    # TODO: implementar lógica em core.py e importar aqui
    return {{"status": "ok", "message": "{name_snake} executado"}}
""")

    functions_code = "\n".join(func_defs)

    return f'''"""
{name} — {description}
MCP server gerado pelo mcp-builder → gerenciado por mcps-as-objects.

ESTE ARQUIVO É GERADO AUTOMATICAMENTE.
Edite core.py para implementar a lógica, não este arquivo.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="{mcp_id}")
{functions_code}

if __name__ == "__main__":
    mcp.run()
'''
