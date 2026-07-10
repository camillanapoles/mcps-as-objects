# Arquitetura — mcps-as-objects

## Conceito

Cada MCP é tratado como um **objeto** com ciclo de vida determinado por um manifesto (`mcp.json`) que segue um schema rígido. O **registry** é o MCP gerente que cataloga, valida, constrói e compõe esses objetos.

```
┌─────────────────────────────────────────────────────────────┐
│                    mcps-as-objects                           │
│                                                             │
│  ┌───────────────────┐     ┌────────────────────────────┐  │
│  │  Filesystem Layer  │     │  Database Layer (SQLite)   │  │
│  │  ┌───────────────┐ │     │  ┌──────────────────────┐ │  │
│  │  │ mcps/<id>/    │ │     │  │ mcps (tabela)        │ │  │
│  │  │  ├─ mcp.json  │ │     │  │ functions (tabela)   │ │  │
│  │  │  ├─ src/      │ │     │  │ runs (tabela)        │ │  │
│  │  │  └─ tests/    │ │     │  └──────────────────────┘ │  │
│  │  └───────────────┘ │     └────────────────────────────┘  │
│  └───────────────────┘                                      │
│           │                         ▲                       │
│           ▼                         │                       │
│  ┌──────────────────────────────────────────────────┐       │
│  │           Registry Backend (Python)              │       │
│  │  ┌──────────┐ ┌──────────┐ ┌────────────────┐   │       │
│  │  │ MCP stdio │ │ HTTP API │ │ CLI (mcpsctl)  │   │       │
│  │  │ (FastMCP) │ │(FastAPI) │ │ (Typer)        │   │       │
│  │  └──────────┘ └──────────┘ └────────────────┘   │       │
│  └──────────────────────────────────────────────────┘       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Camadas

### 1. Filesystem Layer (`mcps/<id>/`)
- Cada MCP em seu diretório
- `mcp.json` é a **única fonte de verdade** sobre o que o MCP faz
- `src/server.py` é a implementação
- `tests/` são os testes
- Determinismo: hash do `mcp.json` vira cache key

### 2. Database Layer (SQLite)
- Persistência de estado entre steps do workflow
- Tabelas: `mcps`, `functions`, `runs`, `migrations`, `catalog_snapshots`
- Migrations versionadas e idempotentes
- DB é cacheado via `actions/cache` entre runs

### 3. Registry Backend
Três interfaces complementares:

| Interface | Transporte | Uso |
|-----------|-----------|-----|
| **MCP stdio** | stdin/stdout | pi-coding, clientes MCP locais |
| **HTTP API** | TCP :8712 | Workflows, curl, testes |
| **CLI** (`mcpsctl`) | terminal | Desenvolvimento local |

## Princípios de Design

1. **Determinismo** — Mesmo input sempre gera mesmo output. Cache key é hash do lockfile + runner.
2. **Schema-first** — Toda validação passa pelo JSON Schema em `schemas/`.
3. **Snapshot** — A máquina de estado (venv + DB) é cacheada para execução subsegunda.
4. **Composição via pipeline** — MCPs declaram `pipeline.consumes` e `pipeline.produces`, permitindo DAG.
5. **Sem estado global** — Cada run é isolada. O DB só guarda metadados e resultados.

## Fluxo de Dados

```
1. mcp.json (fs)  →  catalog.py  →  registro no SQLite
2. CLI/API/MCP    →  validação contra schemas/
3. Constructor    →  template/  →  novo MCP materializado
4. Workflow       →  registry boot  →  matrix workers  →  collect
5. Snapshot       →  cache/restore de .venv + DB
```
