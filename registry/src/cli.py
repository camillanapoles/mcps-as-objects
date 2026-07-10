#!/usr/bin/env python3
"""
mcpsctl — CLI de gestão determinística de MCPs.

Uso:
    mcpsctl list              Listar MCPs catalogados
    mcpsctl describe <id>     Detalhar um MCP
    mcpsctl new <id>          Criar novo MCP a partir do template
    mcpsctl validate <id>     Validar manifesto contra schemas
    mcpsctl validate --all    Validar todos os manifestos
    mcpsctl lock              Atualizar mcps-lock.json
    mcpsctl scan              Escanear filesystem e registrar no DB
    mcpsctl serve-api         Rodar API HTTP
    mcpsctl serve-mcp         Rodar MCP server (stdio)
    mcpsctl cache-key         Mostrar chave de cache determinística
"""

import sys
import json
import typer
from pathlib import Path

# Adiciona src/ ao path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "registry" / "src"))

app = typer.Typer(name="mcpsctl", help="Gestão determinística de MCPs")

# ── Commands ──────────────────────────────────────────────────────


@app.command()
def list():
    """Listar MCPs catalogados."""
    from registry.src import catalog, db, crud
    conn = db.get_conn()
    mcps = crud.list_mcps(conn)
    if not mcps:
        typer.echo("Nenhum MCP registrado.")
        return
    typer.echo(f"{'ID':<30} {'Nome':<30} {'Versão':<12} {'Atualizado'}")
    typer.echo("-" * 85)
    for m in mcps:
        typer.echo(f"{m['id']:<30} {m['name']:<30} {m['version']:<12} {m.get('updated_at','')[:19]}")


@app.command()
def describe(mcp_id: str):
    """Detalhar um MCP."""
    from registry.src import catalog
    man = catalog.read_manifest(mcp_id)
    if not man:
        typer.echo(f"Erro: MCP '{mcp_id}' não encontrado.")
        raise typer.Exit(1)
    typer.echo(json.dumps(man, indent=2, ensure_ascii=False))


@app.command()
def new(mcp_id: str, name: str = typer.Option(None, "--name", "-n"),
        description: str = typer.Option(None, "--desc", "-d"),
        version: str = typer.Option("0.1.0", "--version", "-v")):
    """Criar novo MCP a partir do template."""
    from registry.src import constructor, catalog, db, crud
    try:
        dest = constructor.create_mcp(mcp_id, name, description, version)
        # Atualiza lockfile
        man = catalog.read_manifest(mcp_id)
        if man:
            catalog.update_lock(
                mcp_id=mcp_id,
                version=version,
                manifest_hash=catalog.manifest_hash(mcp_id) or ""
            )
        conn = db.get_conn()
        crud.register_mcp(conn, mcp_id)
        typer.echo(f"✓ MCP '{mcp_id}' criado em {dest}")
        typer.echo(f"  Agora edite: {dest / 'mcp.json'}")
        typer.echo(f"  E implemente: {dest / 'src' / 'server.py'}")
    except (ValueError, FileExistsError) as exc:
        typer.echo(f"Erro: {exc}")
        raise typer.Exit(1)


@app.command()
def validate(mcp_id: str = typer.Argument(None),
             all: bool = typer.Option(False, "--all", "-a")):
    """Validar manifesto contra schemas."""
    from registry.src import validator, catalog

    targets = []
    if all:
        targets = catalog.list_mcp_ids()
        if not targets:
            typer.echo("Nenhum MCP encontrado para validar.")
            return
    elif mcp_id:
        targets = [mcp_id]
    else:
        typer.echo("Informe <id> ou --all")
        raise typer.Exit(1)

    errors_found = 0
    for mid in targets:
        man = catalog.read_manifest(mid)
        if not man:
            typer.echo(f"  ✗ {mid}: manifesto não encontrado")
            errors_found += 1
            continue
        valido, erros = validator.validate_manifest(man)
        if valido:
            typer.echo(f"  ✓ {mid}")
        else:
            typer.echo(f"  ✗ {mid}:")
            for e in erros:
                typer.echo(f"      • {e}")
            errors_found += 1

    if errors_found:
        typer.echo(f"\n{errors_found} MCP(s) com erros.")
        raise typer.Exit(1)
    typer.echo("\nTodos os manifestos válidos.")


@app.command()
def lock():
    """Atualizar mcps-lock.json com hashes atuais."""
    from registry.src import catalog
    lock = catalog.read_lockfile()
    if "entries" not in lock:
        lock["entries"] = {}

    count = 0
    for mid in catalog.list_mcp_ids():
        man = catalog.read_manifest(mid)
        if not man:
            continue
        mhash = catalog.manifest_hash(mid)
        if mhash:
            lock["entries"][mid] = {
                "version": man.get("version", "0.0.0"),
                "manifest_hash": mhash,
                "deps_hash": ""
            }
            count += 1

    catalog.write_lockfile(lock)
    typer.echo(f"✓ Lockfile atualizado com {count} MCP(s)")


@app.command()
def scan():
    """Escanear filesystem e registrar todos os MCPs no DB."""
    from registry.src import db, crud
    conn = db.get_conn()
    count = crud.scan_and_register_all(conn)
    typer.echo(f"✓ {count} MCP(s) registrados no banco.")


@app.command()
def serve_api(host: str = typer.Option("127.0.0.1", "--host"),
              port: int = typer.Option(8712, "--port", "-p"),
              reload: bool = typer.Option(False, "--reload")):
    """Rodar API HTTP (uvicorn)."""
    import uvicorn
    uvicorn.run("registry.src.api:app", host=host, port=port, reload=reload)


@app.command()
def serve_mcp():
    """Rodar MCP server (stdio)."""
    from registry.src import server
    server.mcp.run()


@app.command(name="cache-key")
def cache_key():
    """Mostrar chave de cache determinística."""
    from registry.src import snapshot
    key = snapshot.compute_cache_key()
    typer.echo(key)


def main():
    """Entrypoint."""
    app()


if __name__ == "__main__":
    main()
