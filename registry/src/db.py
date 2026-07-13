"""
Database layer — SQLite com migrations.
Design: singletone de conexão com schema versionado.
"""

import sqlite3
import json
import os
import hashlib
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "registry.db"


def _get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    db = db_path or DB_PATH
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def run_migrations(conn: Optional[sqlite3.Connection] = None):
    """Executa migrations idempotentes."""
    close = conn is None
    conn = conn or _get_connection()

    # Cria tabela de controle de migrations
    conn.execute("""
        CREATE TABLE IF NOT EXISTS migrations (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    migrations = [
        (1, _migration_001_initial),
        (2, _migration_002_add_mcp_fields),
    ]

    current = conn.execute("SELECT COALESCE(MAX(version), 0) FROM migrations").fetchone()[0]

    for ver, fn in migrations:
        if ver > current:
            fn(conn)
            conn.execute("INSERT INTO migrations (version) VALUES (?)", (ver,))
            conn.commit()

    if close:
        conn.close()


def _migration_001_initial(conn: sqlite3.Connection):
    """Cria as tabelas iniciais."""
    conn.executescript("""
        CREATE TABLE mcps (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            version TEXT NOT NULL,
            description TEXT DEFAULT '',
            manifest_path TEXT NOT NULL,
            manifest_hash TEXT NOT NULL,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE functions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mcp_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            input_schema TEXT NOT NULL DEFAULT '{}',
            output_schema TEXT NOT NULL DEFAULT '{}',
            FOREIGN KEY (mcp_id) REFERENCES mcps(id),
            UNIQUE (mcp_id, name)
        );

        CREATE TABLE runs (
            id TEXT PRIMARY KEY,
            mcp_id TEXT NOT NULL,
            function_name TEXT NOT NULL,
            input_payload TEXT DEFAULT '{}',
            output_payload TEXT,
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending','ok','error')),
            started_at TIMESTAMP,
            finished_at TIMESTAMP,
            workflow_run_id TEXT,
            FOREIGN KEY (mcp_id) REFERENCES mcps(id)
        );

        CREATE TABLE catalog_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_hash TEXT NOT NULL,
            data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)


def _migration_002_add_mcp_fields(conn: sqlite3.Connection):
    """Adiciona colunas status, production_enabled e sdk à tabela mcps."""
    # Add columns if they don't exist (SQLite doesn't support IF NOT EXISTS for ALTER, so catch errors)
    for col, coltype in [
        ("status", "TEXT NOT NULL DEFAULT 'TODO'"),
        ("production_enabled", "INTEGER NOT NULL DEFAULT 0"),
        ("sdk", "TEXT NOT NULL DEFAULT 'python'"),
    ]:
        try:
            conn.execute(f"ALTER TABLE mcps ADD COLUMN {col} {coltype}")
        except sqlite3.OperationalError:
            pass  # Column already exists


def compute_manifest_hash(manifest_path: Path) -> str:
    """SHA-256 do conteúdo do manifesto."""
    data = manifest_path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def get_conn(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Retorna conexão com migrations aplicadas."""
    conn = _get_connection(db_path)
    run_migrations(conn)
    return conn
