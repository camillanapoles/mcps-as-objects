#!/usr/bin/env bash
#
# snapshot.sh — Gera / restaura snapshot de máquina MCP para cache.
# Uso: source tools/snapshot.sh && save_snapshot|restore_snapshot
#
# Design: A chave de cache é derivada deterministicamente do lockfile
# + hash do runner OS. Mesmo manifest → mesmo cache hit.
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

snapshot_key() {
  # Produz uma chave de cache determinística
  local lock_hash runner_hash
  lock_hash="${1:-$(sha256sum "$ROOT/mcps-lock.json" 2>/dev/null | cut -d' ' -f1)}"
  runner_hash="$(uname -a | sha256sum | cut -d' ' -f1 | head -c 12)"
  echo "mcp-snapshot-${lock_hash}-${runner_hash}"
}

restore_snapshot() {
  local cache_dir="$ROOT/.cache/snapshot"
  if [ ! -d "$cache_dir" ]; then
    echo "[snapshot] Nenhum cache local em $cache_dir"
    return 1
  fi
  echo "[snapshot] Restaurando de $cache_dir..."
  cp -a "$cache_dir/." "$ROOT/"
  echo "[snapshot] ✓ Restaurado"
}

save_snapshot() {
  local cache_dir="$ROOT/.cache/snapshot"
  local snap_key
  snap_key="$(snapshot_key)"

  echo "[snapshot] Salvando snapshot key=$snap_key..."

  mkdir -p "$cache_dir"
  # Salva venv + DB
  if [ -d "$ROOT/.venv" ]; then
    mkdir -p "$cache_dir/.venv"
    cp -a "$ROOT/.venv/." "$cache_dir/.venv/"
  fi
  if [ -f "$ROOT/registry/data/registry.db" ]; then
    mkdir -p "$cache_dir/registry/data"
    cp "$ROOT/registry/data/registry.db" "$cache_dir/registry/data/"
  fi
  # Salva mcps-lock como fingerprint
  cp "$ROOT/mcps-lock.json" "$cache_dir/"

  echo "[snapshot] ✓ Salvo. Key: $snap_key"
  echo ""
  echo "  Para usar em GitHub Actions, adicione:"
  echo "  - uses: actions/cache@v4"
  echo "    with:"
  echo "      path: .cache/snapshot"
  echo "      key: $snap_key"
}

# Se chamado diretamente (não sourceado)
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  case "${1:-}" in
    key)    snapshot_key "${2:-}" ;;
    save)   save_snapshot ;;
    restore) restore_snapshot ;;
    *)
      echo "Uso: source tools/snapshot.sh"
      echo "     snapshot.sh (key|save|restore)"
      exit 1
      ;;
  esac
fi
