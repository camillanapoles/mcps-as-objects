"""
Testes de fumaça para o registry.
"""

import sys
import json
import tempfile
from pathlib import Path

# Add registry/src to path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "registry" / "src"))

from registry.src import db, validator, catalog, constructor, snapshot


class TestDB:
    def test_get_conn(self):
        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            conn = db.get_conn(Path(f.name))
            # Tabelas devem existir
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = [t["name"] for t in tables]
            assert "mcps" in table_names
            assert "functions" in table_names
            assert "runs" in table_names
            assert "migrations" in table_names
            conn.close()

    def test_migrations_idempotent(self):
        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            p = Path(f.name)
            conn1 = db.get_conn(p)
            migs1 = conn1.execute("SELECT COUNT(*) as c FROM migrations").fetchone()["c"]
            conn1.close()
            conn2 = db.get_conn(p)
            migs2 = conn2.execute("SELECT COUNT(*) as c FROM migrations").fetchone()["c"]
            assert migs1 == migs2, "Migrations devem ser idempotentes"
            conn2.close()


class TestValidator:
    def test_valid_manifest(self):
        """Manifesto do example-greeter deve ser válido."""
        man_path = ROOT / "mcps" / "example-greeter" / "mcp.json"
        assert man_path.exists(), f"Não encontrado: {man_path}"
        valido, erros = validator.validate_manifest_file(man_path)
        assert valido, f"Era válido mas falhou: {erros}"

    def test_invalid_manifest_missing_field(self):
        """Manifesto sem campos obrigatórios deve falhar."""
        man = {"id": "test"}
        valido, erros = validator.validate_manifest(man)
        assert not valido
        assert any("'name'" in e for e in erros)


class TestCatalog:
    def test_list_includes_example(self):
        ids = catalog.list_mcp_ids()
        assert "example-greeter" in ids

    def test_read_manifest(self):
        man = catalog.read_manifest("example-greeter")
        assert man is not None
        assert man["id"] == "example-greeter"
        assert len(man["functions"]) == 2

    def test_manifest_hash(self):
        h = catalog.manifest_hash("example-greeter")
        assert h and len(h) == 64


class TestConstructor:
    def test_create_mcp(self):
        with tempfile.TemporaryDirectory() as tmp:
            from unittest.mock import patch
            # Redireciona MCPS_DIR para diretório temporário
            original_root = catalog.ROOT
            catalog.ROOT = Path(tmp)

            try:
                dest = constructor.create_mcp("test-mcp", "Test MCP", "MCP de teste")
                assert dest.exists()
                assert (dest / "mcp.json").exists()
                assert (dest / "src" / "server.py").exists()
                assert (dest / "tests" / "test_smoke.py").exists()
                # Verifica manifesto
                man = json.loads((dest / "mcp.json").read_text())
                assert man["id"] == "test-mcp"
                assert man["name"] == "Test MCP"
            finally:
                catalog.ROOT = original_root

    def test_create_mcp_invalid_id(self):
        import re
        try:
            constructor.create_mcp("ID Invalido!")
            assert False, "Deveria ter lançado ValueError"
        except ValueError:
            pass


class TestSnapshot:
    def test_cache_key_generation(self):
        key = snapshot.compute_cache_key()
        assert key.startswith("mcp-snapshot-v1-")
        assert len(key) > 30
