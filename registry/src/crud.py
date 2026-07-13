"""
CRUD — operações no banco SQLite.
Sempre em conjunto com catalog.py (filesystem) e validator.py.
"""

import json
import sqlite3
from typing import Optional, Dict, List
import db
import catalog


# ── MCPs ──────────────────────────────────────────────────────────

def register_mcp(conn: sqlite3.Connection, mcp_id: str) -> Optional[dict]:
    """Registra ou atualiza um MCP no DB a partir do manifesto no filesystem."""
    man = catalog.read_manifest(mcp_id)
    if not man:
        return None

    mhash = catalog.manifest_hash(mcp_id)
    manifest_path = str(catalog.ROOT / mcp_id / "mcp.json")
    conn.execute("""
        INSERT INTO mcps (id, name, version, description, manifest_path, manifest_hash, status, production_enabled, sdk)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            version=excluded.version,
            description=excluded.description,
            manifest_path=excluded.manifest_path,
            manifest_hash=excluded.manifest_hash,
            sdk=excluded.sdk,
            updated_at=CURRENT_TIMESTAMP
    """, (mcp_id, man["name"], man["version"], man.get("description", ""),
          manifest_path, mhash,
          man.get("status", "TODO"),
          man.get("production_enabled", False),
          man.get("sdk", "python")))

    # Atualiza funções
    conn.execute("DELETE FROM functions WHERE mcp_id = ?", (mcp_id,))
    for fn in man.get("functions", []):
        conn.execute("""
            INSERT INTO functions (mcp_id, name, description, input_schema, output_schema)
            VALUES (?, ?, ?, ?, ?)
        """, (
            mcp_id,
            fn["name"],
            fn.get("description", ""),
            json.dumps(fn.get("input_schema", {})),
            json.dumps(fn.get("output_schema", {}))
        ))

    conn.commit()
    return man


def scan_and_register_all(conn: sqlite3.Connection) -> int:
    """Escaneia todos os MCPs no filesystem e registra no DB. Retorna qtd."""
    count = 0
    for mid in catalog.list_mcp_ids():
        if register_mcp(conn, mid):
            count += 1
    return count


def list_mcps(conn: sqlite3.Connection) -> List[dict]:
    """Lista todos os MCPs registrados."""
    rows = conn.execute("SELECT * FROM mcps ORDER BY id").fetchall()
    return [dict(r) for r in rows]


def get_mcp(conn: sqlite3.Connection, mcp_id: str) -> Optional[dict]:
    """Retorna um MCP pelo id."""
    row = conn.execute("SELECT * FROM mcps WHERE id = ?", (mcp_id,)).fetchone()
    return dict(row) if row else None


def delete_mcp(conn: sqlite3.Connection, mcp_id: str) -> bool:
    """Remove um MCP do DB (não do filesystem)."""
    cur = conn.execute("DELETE FROM mcps WHERE id = ?", (mcp_id,))
    conn.commit()
    return cur.rowcount > 0
def update_mcp_status(conn: sqlite3.Connection, mcp_id: str, status: str) -> bool:
    """Update the status of an MCP."""
    cursor = conn.execute(
        """
        UPDATE mcps SET status = ? WHERE id = ?
        """,
        (status, mcp_id),
    )
    return cursor.rowcount > 0



# ── Functions ─────────────────────────────────────────────────────

def list_functions(conn: sqlite3.Connection, mcp_id: str) -> List[dict]:
    """Lista funções de um MCP."""
    rows = conn.execute(
        "SELECT * FROM functions WHERE mcp_id = ? ORDER BY name", (mcp_id,)
    ).fetchall()
    return [dict(r) for r in rows]


# ── Runs ──────────────────────────────────────────────────────────

def create_run(conn: sqlite3.Connection, mcp_id: str, function_name: str,
               input_payload: dict, workflow_run_id: str = "") -> str:
    """Cria um registro de execução. Retorna o id da run."""
    import uuid
    run_id = str(uuid.uuid4())
    conn.execute("""
        INSERT INTO runs (id, mcp_id, function_name, input_payload, status, workflow_run_id)
        VALUES (?, ?, ?, ?, 'pending', ?)
    """, (run_id, mcp_id, function_name, json.dumps(input_payload), workflow_run_id))
    conn.commit()
    return run_id


def finish_run(conn: sqlite3.Connection, run_id: str, output_payload: dict,
               status: str = "ok"):
    """Finaliza uma run com output e status."""
    from datetime import datetime, timezone
    conn.execute("""
        UPDATE runs SET
            output_payload = ?,
            status = ?,
            finished_at = ?
        WHERE id = ?
    """, (json.dumps(output_payload), status, datetime.now(timezone.utc).isoformat(), run_id))
    conn.commit()
