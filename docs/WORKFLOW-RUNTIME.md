# Workflow Runtime — Execução em GitHub Actions

## Visão Geral

O workflow `mcp-runtime.yml` executa todos os MCPs catalogados como **jobs isolados** (máquinas efêmeras), com o registry como ponto central.

## Arquitetura do Workflow

```
Job 0: registry ─┬─ output: mcp_ids ──▶ matrix.strategy.mcp_id
                  │
                  ├─ Restore cache (snapshot)
                  ├─ Boot SQLite + register MCPs
                  └─ Save snapshot

    ┌─────────────┤
    ▼             ▼               ▼
Job 1:     Job 2:            Job N:
worker     worker            worker
mcp-a      mcp-b             mcp-c
    │         │               │
    └─────────┴──────┬────────┘
                     ▼
            Job final: collect
                Consolida resultados
                Upload artifacts
```

## Cache Inteligente

### Estratégia

- **Key**: `mcp-snapshot-v1-{sha256(mcps-lock.json)}-{sha256(uname)[:12]}`
- **Hit**: restaura `.venv` + `registry.db` instantaneamente (~1s vs ~3min para instalar do zero)
- **Miss**: instala dependências, constrói DB, salva snapshot

### Invalidação

O cache é invalidado quando:
- `mcps-lock.json` muda (novo MCP, versão alterada, função alterada)
- Runner OS muda (diferente `uname -a`)
- Forçado via `workflow_dispatch`

## Matrix Strategy

Cada MCP listado no lockfile vira um job separado:

```yaml
jobs:
  worker:
    strategy:
      matrix:
        mcp_id: ${{ fromJSON(needs.registry.outputs.mcp_ids) }}
```

Isso permite:
- Execução paralela de MCPs independentes
- Falha isolada (um MCP quebrado não afeta outros)
- Reuso do mesmo snapshot em todos os workers

## Comunicação entre Jobs

| Fluxo | Mecanismo |
|-------|-----------|
| Registry → Workers | Outputs do job `registry` |
| Workers → Collect | Artifacts (`upload-artifact`) |
| Workers consultam API | Invocam API do registry em `http://localhost:8712` (se rodar em service container) |

## Registro de Runs

Cada execução de MCP cria um registro em `runs` no SQLite:

```sql
INSERT INTO runs (id, mcp_id, function_name, input_payload, status, workflow_run_id)
VALUES (?, ?, ?, ?, 'pending', ?);
```

## Snapshot Local (dev)

```bash
source tools/snapshot.sh
save_snapshot     # Salva .venv + DB em .cache/snapshot/
restore_snapshot  # Restaura de .cache/snapshot/
snapshot_key      # Mostra chave atual
```
