"""
Snapshot — lógica de cache key determinística.
A chave combina:
  - Hash do mcps-lock.json (contém hash do manifesto de cada MCP)
  - Hash do runner (uname -a)
  - Versão do formato (para invalidar caches antigos)
"""

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
LOCKFILE = ROOT / "mcps-lock.json"


def compute_cache_key() -> str:
    """Chave determinística para snapshot/cache."""
    lock_data = LOCKFILE.read_bytes() if LOCKFILE.exists() else b"{}"
    lock_hash = hashlib.sha256(lock_data).hexdigest()

    runner_data = _get_runner_fingerprint()
    runner_hash = hashlib.sha256(runner_data).hexdigest()[:12]

    return f"mcp-snapshot-v1-{lock_hash}-{runner_hash}"


def _get_runner_fingerprint() -> bytes:
    """Retorna fingerprint do runner (uname -a ou placeholder)."""
    import subprocess
    try:
        result = subprocess.run(["uname", "-a"], capture_output=True, text=True, timeout=5)
        return result.stdout.encode() if result.returncode == 0 else b"unknown-runner"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return b"unknown-runner"


def verify_cache_key(lockfile_hash: str, runner_hash: str) -> bool:
    """
    Verifica se uma key de cache é válida contra o estado atual.
    Útil para GitHub Actions: compara com a key armazenada.
    """
    current = compute_cache_key()
    expected = f"mcp-snapshot-v1-{lockfile_hash}-{runner_hash}"
    return current == expected
