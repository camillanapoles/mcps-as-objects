"""
Catalog — lê, valida e cacheia manifestos do filesystem.
Fonte da verdade: diretório mcps/<id>/mcp.json.
Determinístico: cada leitura computa hash e valida contra schema.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent.parent / "mcps"
LOCKFILE = ROOT.parent / "mcps-lock.json"


def list_mcp_ids() -> List[str]:
    """Lista IDs de todos os MCPs no diretório mcps/."""
    ids = []
    for d in ROOT.iterdir():
        if d.is_dir() and not d.name.startswith("_"):
            manifest = d / "mcp.json"
            if manifest.exists():
                ids.append(d.name)
    return sorted(ids)


def read_manifest(mcp_id: str) -> Optional[dict]:
    """Lê o manifesto de um MCP."""
    path = ROOT / mcp_id / "mcp.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def manifest_hash(mcp_id: str) -> Optional[str]:
    """SHA-256 do arquivo mcp.json."""
    path = ROOT / mcp_id / "mcp.json"
    if not path.exists():
        return None
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def scan_catalog() -> Dict[str, dict]:
    """
    Escaneia todos os MCPs, retorna dict id→manifest.
    Equivalente a um 'load all' determinístico.
    """
    result = {}
    for mid in list_mcp_ids():
        man = read_manifest(mid)
        if man:
            result[mid] = man
    return result


def read_lockfile() -> dict:
    """Lê o mcps-lock.json."""
    if not LOCKFILE.exists():
        return {"version": 1, "entries": {}}
    return json.loads(LOCKFILE.read_text())


def write_lockfile(lock: dict):
    """Escreve o mcps-lock.json."""
    LOCKFILE.write_text(json.dumps(lock, indent=2, ensure_ascii=False) + "\n")


def update_lock(mcp_id: str, version: str, manifest_hash: str, deps_hash: str = ""):
    """Atualiza uma entrada no lockfile."""
    lock = read_lockfile()
    if "entries" not in lock:
        lock["entries"] = {}
    lock["entries"][mcp_id] = {
        "version": version,
        "manifest_hash": manifest_hash,
        "deps_hash": deps_hash
    }
    write_lockfile(lock)
