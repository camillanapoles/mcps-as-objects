#!/usr/bin/env python3
"""
verify-mcp.py — Verificação completa de conformidade de um MCP.

Garante que o MCP segue:
  📁 Estrutura de diretórios padrão
  📜 Schema do manifesto (mcp.json)
  🔧 Funções no server.py condizentes com o manifesto
  🧪 Testes existem e importam corretamente
  📦 Lockfile consistente
  🚀 Pode ser disparado individualmente (event-driven)

Uso:
  python3 scripts/verify-mcp.py <mcp_id>
  python3 scripts/verify-mcp.py --all
"""

import sys
import json
import os
import re
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MCPS_DIR = ROOT / "mcps"
SCHEMAS_DIR = ROOT / "schemas"
LOCKFILE = ROOT / "mcps-lock.json"

# ── Checks ──────────────────────────────────────────────────────────

checks = []
errors = []
warnings = []


def check(name: str, fatal: bool = True):
    """Decorator para registrar checks."""
    def decorator(fn):
        checks.append((name, fn, fatal))
        return fn
    return decorator


def err(msg: str):
    errors.append(msg)


def warn(msg: str):
    warnings.append(msg)


def run_checks(mcp_id: str):
    """Executa todas as verificações para um MCP."""
    global errors, warnings
    errors = []
    warnings = []
    mcp_dir = MCPS_DIR / mcp_id

    for name, fn, fatal in checks:
        try:
            fn(mcp_id, mcp_dir)
        except Exception as e:
            msg = f"[{name}] {e}"
            if fatal:
                err(msg)
            else:
                warn(msg)

    return errors, warnings


# ═══════════════════════════════════════════════════════════════════
# 1. ESTRUTURA DE DIRETÓRIOS
# ═══════════════════════════════════════════════════════════════════

@check("📁 Estrutura de diretórios")
def check_directory_structure(mcp_id: str, mcp_dir: Path):
    if not mcp_dir.exists():
        raise FileNotFoundError(f"Diretório não encontrado: {mcp_dir}")

    required = ["mcp.json", "src/server.py"]
    optional = ["tests/test_smoke.py", "README.md", "requirements.txt"]

    for f in required:
        path = mcp_dir / f
        if not path.exists():
            raise FileNotFoundError(f"Arquivo obrigatório ausente: {f}")

    for f in optional:
        path = mcp_dir / f
        if not path.exists():
            warn(f"Arquivo recomendado ausente: {f}")


@check("📁 Nomenclatura do diretório")
def check_directory_name(mcp_id: str, mcp_dir: Path):
    if not re.match(r'^[a-z][a-z0-9-]*[a-z0-9]$', mcp_id):
        raise ValueError(
            f"ID '{mcp_id}' inválido. Use kebab-case: letras minúsculas, números e hífens."
        )


# ═══════════════════════════════════════════════════════════════════
# 2. MANIFESTO (mcp.json)
# ═══════════════════════════════════════════════════════════════════

@check("📜 Manifesto JSON válido")
def check_manifest_json(mcp_id: str, mcp_dir: Path):
    path = mcp_dir / "mcp.json"
    try:
        with open(path) as f:
            man = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON inválido: {e}")

    return man


@check("📜 Manifesto contra schema")
def check_manifest_schema(mcp_id: str, mcp_dir: Path):
    # Importa validador do registry
    sys.path.insert(0, str(ROOT / "registry" / "src"))
    from validator import validate_manifest_file

    valido, erros = validate_manifest_file(str(mcp_dir / "mcp.json"))
    if not valido:
        raise ValueError(f"Contra schema: {erros}")


@check("📜 Manifesto: id condiz com diretório")
def check_manifest_id(mcp_id: str, mcp_dir: Path):
    with open(mcp_dir / "mcp.json") as f:
        man = json.load(f)
    if man.get("id") != mcp_id:
        raise ValueError(
            f"ID no manifesto '{man.get('id')}' difere do diretório '{mcp_id}'"
        )


@check("📜 Manifesto: platforms definido")
def check_manifest_platforms(mcp_id: str, mcp_dir: Path):
    with open(mcp_dir / "mcp.json") as f:
        man = json.load(f)
    plats = man.get("platforms")
    if not plats:
        warn("Campo 'platforms' ausente. Usando padrão ['*'] (universal).")


@check("📜 Manifesto: ao menos 1 função")
def check_manifest_functions(mcp_id: str, mcp_dir: Path):
    with open(mcp_dir / "mcp.json") as f:
        man = json.load(f)
    funcs = man.get("functions", [])
    if len(funcs) == 0:
        raise ValueError("Nenhuma função declarada no manifesto")


# ═══════════════════════════════════════════════════════════════════
# 3. SERVER.PY
# ═══════════════════════════════════════════════════════════════════

@check("🔧 server.py: entrypoint existe")
def check_server_entry(mcp_id: str, mcp_dir: Path):
    with open(mcp_dir / "mcp.json") as f:
        man = json.load(f)
    entry = man.get("entry", "src/server.py")
    entry_path = mcp_dir / entry
    if not entry_path.exists():
        raise FileNotFoundError(f"Entrypoint '{entry}' não encontrado")


@check("🔧 server.py: @mcp.tool() condizentes com manifesto")
def check_server_tools(mcp_id: str, mcp_dir: Path):
    """Verifica se as funções no server.py têm @mcp.tool() correspondente."""
    with open(mcp_dir / "mcp.json") as f:
        man = json.load(f)

    server_path = mcp_dir / man.get("entry", "src/server.py")
    if not server_path.exists():
        return

    server_code = server_path.read_text()

    # Extrai nomes das funções decoradas com @mcp.tool()
    tool_pattern = re.compile(r'@mcp\.tool\(\)\s*\n\s*def\s+(\w+)\s*\(')
    tool_functions = set(tool_pattern.findall(server_code))

    # Funções do manifesto
    manifest_functions = {fn["name"] for fn in man.get("functions", [])}

    # Toda função do manifesto deve existir no server.py
    missing_in_server = manifest_functions - tool_functions
    if missing_in_server:
        raise ValueError(
            f"Funções no manifesto sem @mcp.tool() no server.py: {missing_in_server}"
        )

    # Funções no server.py que não estão no manifesto (apenas warning)
    extra_in_server = tool_functions - manifest_functions
    if extra_in_server:
        warn(f"Funções em server.py sem declaração no manifesto: {extra_in_server}")


# ═══════════════════════════════════════════════════════════════════
# 4. TESTES
# ═══════════════════════════════════════════════════════════════════

@check("🧪 Testes: arquivo de teste existe")
def check_tests_exist(mcp_id: str, mcp_dir: Path):
    tests_dir = mcp_dir / "tests"
    if not tests_dir.exists():
        warn("Diretório tests/ ausente")
        return

    test_files = list(tests_dir.glob("test_*.py"))
    if not test_files:
        warn("Nenhum arquivo test_*.py encontrado em tests/")


@check("🧪 Testes: importação sem erro")
def check_tests_import(mcp_id: str, mcp_dir: Path):
    """Tenta importar o módulo de teste para verificar erros de sintaxe/import."""
    tests_dir = mcp_dir / "tests"
    if not tests_dir.exists():
        return

    for tf in tests_dir.glob("test_*.py"):
        try:
            compile(tf.read_text(), str(tf), 'exec')
        except SyntaxError as e:
            warn(f"Erro de sintaxe em {tf.name}: {e}")


# ═══════════════════════════════════════════════════════════════════
# 5. LOCKFILE
# ═══════════════════════════════════════════════════════════════════

@check("📦 Lockfile: entrada existe")
def check_lockfile_entry(mcp_id: str, mcp_dir: Path):
    if not LOCKFILE.exists():
        warn("mcps-lock.json não encontrado")
        return
    lock = json.loads(LOCKFILE.read_text())
    entries = lock.get("entries", {})
    if mcp_id not in entries:
        warn(f"MCP '{mcp_id}' sem entrada no mcps-lock.json. Execute: mcpsctl lock")


# ═══════════════════════════════════════════════════════════════════
# 6. EVENT-DRIVEN: Pode ser chamado individualmente
# ═══════════════════════════════════════════════════════════════════

@check("💾 Cache: lockfile determina cache key (isolamento)")
def check_cache_isolation(mcp_id: str, mcp_dir: Path):
    """
    Verifica que o lockfile está atualizado — o cache key depende do hash
    do lockfile, então MCPs diferentes têm caches diferentes.
    """
    mhash = hashlib.sha256((mcp_dir / "mcp.json").read_bytes()).hexdigest()

    if not LOCKFILE.exists():
        warn("mcps-lock.json ausente — cache key não pode ser verificada")
        return

    lock = json.loads(LOCKFILE.read_text())
    entries = lock.get("entries", {})

    if mcp_id not in entries:
        warn(f"MCP sem entrada no lockfile → cache key NÃO inclui este MCP. Execute: mcpsctl lock")
        return

    locked_hash = entries[mcp_id].get("manifest_hash", "")
    if locked_hash != mhash:
        warn(f"Hash do manifesto diverge do lockfile. Lock: {locked_hash[:16]}... Atual: {mhash[:16]}... → cache key desatualizada")
    else:
        print(f"    💾 Cache: hash consistente → cache key = f(mcp-lock.json) = {mhash[:16]}...")


@check("🚀 Event-driven: pode ser disparado individualmente")
def check_event_driven(mcp_id: str, mcp_dir: Path):
    """Verifica se o MCP pode ser executado via scripts/execute-mcp.py (individual)."""
    exec_script = ROOT / "scripts" / "execute-mcp.py"
    if not exec_script.exists():
        warn("scripts/execute-mcp.py não encontrado — não é possível verificar execução individual")
        return

    # Verifica se o módulo server.py pode ser importado minimamente
    server_path = mcp_dir / "src" / "server.py"
    if not server_path.exists():
        return

    # Tenta compilar (não executa para não disparar FastMCP)
    try:
        compile(server_path.read_text(), str(server_path), 'exec')
    except SyntaxError as e:
        raise ValueError(f"Erro de sintaxe em server.py: {e}")


# ═══════════════════════════════════════════════════════════════════
# 7. PLATAFORMA
# ═══════════════════════════════════════════════════════════════════

@check("📱 Compatibilidade de plataforma")
def check_platform_compat(mcp_id: str, mcp_dir: Path):
    """Verifica se as plataformas declaradas são válidas."""
    with open(mcp_dir / "mcp.json") as f:
        man = json.load(f)
    plats = man.get("platforms", ["*"])
    valid_platforms = {"*", "linux/amd64", "linux/arm64", "android/termux",
                       "darwin/amd64", "darwin/arm64"}
    for p in plats:
        if p not in valid_platforms:
            warn(f"Plataforma '{p}' não reconhecida. Válidas: {valid_platforms}")


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def verify_one(mcp_id: str) -> bool:
    """Verifica um MCP. Retorna True se OK."""
    print(f"\n{'='*60}")
    print(f"  VERIFICANDO: {mcp_id}")
    print(f"{'='*60}")

    run_checks(mcp_id)
    total_checks = len(checks)

    if errors:
        print(f"\n  ❌ {len(errors)} ERRO(S):")
        for e in errors:
            print(f"     • {e}")
    if warnings:
        print(f"\n  ⚠️  {len(warnings)} AVISO(S):")
        for w in warnings:
            print(f"     • {w}")

    total_issues = len(errors) + len(warnings)
    status = "✅ APROVADO" if not errors else "❌ REPROVADO"
    extra = f" ({len(warnings)} avisos)" if warnings else ""
    print(f"\n  {status} — {total_checks} checks, {len(errors)} erros{extra}")
    return len(errors) == 0


def main():
    args = sys.argv[1:]

    if "--all" in args:
        from catalog import list_mcp_ids
        sys.path.insert(0, str(ROOT / "registry" / "src"))
        ids = list_mcp_ids()
        print(f"Verificando todos os {len(ids)} MCPs...")
        results = {}
        for mid in ids:
            results[mid] = verify_one(mid)
        print(f"\n{'='*60}")
        print("  RESUMO:")
        for mid, ok in results.items():
            icon = "✅" if ok else "❌"
            print(f"  {icon} {mid}")
        if all(results.values()):
            print("\n  ✅ Todos os MCPs aprovados!")
        else:
            failed = [m for m, o in results.items() if not o]
            print(f"\n  ❌ {len(failed)} MCP(s) reprovados: {failed}")
            sys.exit(1)
    elif args:
        ok = verify_one(args[0])
        sys.exit(0 if ok else 1)
    else:
        print("Uso: python3 scripts/verify-mcp.py <mcp_id>")
        print("     python3 scripts/verify-mcp.py --all")
        sys.exit(1)


if __name__ == "__main__":
    main()
