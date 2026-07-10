#!/usr/bin/env bash
#
# bootstrap.sh — Inicializa o ambiente mcps-as-objects do zero.
# Uso: ./tools/bootstrap.sh [--no-install]
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "╔══════════════════════════════════════════════╗"
echo "║  mcps-as-objects — Bootstrap                 ║"
echo "╚══════════════════════════════════════════════╝"

# ── Python & Virtualenv ──────────────────────────────
echo "[1/4] Verificando Python 3.11+..."
PY="python3"
if ! command -v "$PY" &>/dev/null; then
  echo "[!] Python3 não encontrado." >&2
  exit 1
fi
PY_VER=$($PY -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "      Python $PY_VER — OK"

if [ ! -f .venv/bin/python3 ]; then
  echo "[2/4] Criando virtualenv..."
  $PY -m venv .venv
fi
.venv/bin/pip install --upgrade pip -q

echo "[3/4] Instalando dependências..."
.venv/bin/pip install -r requirements.txt -q

chmod +x tools/mcpsctl

echo "[4/4] Verificando..."
tools/mcpsctl validate --all 2>/dev/null && echo "      ✓ Manifestos válidos" || echo "      (seed) Primeiro MCP precisa ser criado"

# ── Resumo ───────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  Pronto!                                      ║"
echo "║                                                ║"
echo "║  Comandos:                                     ║"
echo "║    make install     (instalar deps)            ║"
echo "║    make run-api     (API CRUD :8712)           ║"
echo "║    make run-mcp     (MCP server stdio)         ║"
echo "║    make test        (testes)                   ║"
echo "║                                                ║"
echo "║  tools/mcpsctl:                                ║"
echo "║    list             (listar MCPs)              ║"
echo "║    describe <id>    (detalhar MCP)             ║"
echo "║    new <id>         (criar novo MCP)           ║"
echo "║    validate <id>    (validar manifesto)        ║"
echo "║    lock             (atualizar mcps-lock.json) ║"
echo "╚══════════════════════════════════════════════╝"
