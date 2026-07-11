# 🏗️ Plano de Integração: mcp-builder → mcps-as-objects

> **Bridge + Adapter + Compliance — Zero Hardcoded, 100% Gerenciado, Agnóstico, Replicável.**

---

## ═══════════════════════════════════════════════════════════════════
## 1. VISÃO GERAL
## ═══════════════════════════════════════════════════════════════════

```
ESTADO ATUAL:                           ESTADO DESEJADO:
─────────────────                       ─────────────────
mcp-builder (CRIA)                      mcp-builder (CRIA)
  │                                        │
  └─ Gera projeto em disco                 ├─ Gera projeto
                                          │
mcps-as-objects (GERENCIA)                ├─ ADAPTER → bridge
  │                                        │    ├─ Lê blueprint.yaml
  └─ Registry + DB + API + Cache           │    ├─ Gera mcp.json
                                          │    ├─ Gera server.py
INTEGRAÇÃO: ❌ NÃO EXISTE                  │    └─ Valida + registra
                                          │
                                          ▼
                                        mcps-as-objects (GERENCIA)
                                          │
                                          └─ Registry + DB + API
                                             Cache + Verify + Dispatch

COBERTURA DE ESCOPO: 40% + 40% = 80%     COBERTURA: ~98%
(faltou bridge)                           (só falta edge cases)
```

---

## ═══════════════════════════════════════════════════════════════════
## 2. PRINCÍPIOS DE COMPLIANCE (NÃO NEGOCIÁVEIS)
## ═══════════════════════════════════════════════════════════════════

| # | Princípio | O que significa | Como garantir |
|---|-----------|-----------------|---------------|
| **P1** | Zero Hardcoded | Nenhum valor fixo no código. Tudo vem de DB, API POST, API GET, inputs | Adapter lê `blueprint.yaml` + manifesto → gera tudo dinamicamente |
| **P2** | 100% Gerenciado | Todo MCP tem entrada no DB, manifesto, lockfile, verify | Adapter chama `register_mcp()` + `verify-mcp()` + `mcpsctl lock` |
| **P3** | Agnóstico | Funciona com qualquer SDK (Python, TS, Go, Rust) e qualquer padrão (stateless, event, factory) | Template engine do mcp-builder já é 4×3. Adapter é polyglota |
| **P4** | Replicável em qualquer ambiente | Mesmo input + mesmo blueprint → mesmo output. Em Termux, GitHub Actions, dev local | Adapter é determinístico. Cache SHA-256. FSM com states.yaml |
| **P5** | Auditável | Toda ação registrada: quem criou, quando, workflow run_id, hash do manifesto | SQLite + mcps-lock.json + runs table |
| **P6** | Testado | Todo MCP gerado tem testes que passam antes de registrar | Adapter executa pytest + verify-mcp (15 checks) |
| **P7** | Plataforma explícita | Todo MCP declara onde funciona | `platforms` no mcp.json. Adapter infere do blueprint |
| **P8** | Event-driven | Cada MCP responde ao seu próprio evento | Adapter registra no DB → `POST /dispatch` disponível imediatamente |

---

## ═══════════════════════════════════════════════════════════════════
## 3. ARQUITETURA DA INTEGRAÇÃO
## ═══════════════════════════════════════════════════════════════════

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ECOSSISTEMA COMPLETO                          │
│                                                                     │
│  ┌────────────────────────┐    ┌───────────────────────────────┐   │
│  │   mcp-builder          │    │     mcps-as-objects            │   │
│  │                        │    │                               │   │
│  │  CLI: npx mcp-builder  │    │  Registry API :8712           │   │
│  │  MCP server            │    │  MCP server (stdio)           │   │
│  │  HTTP API :3000        │    │  CLI: tools/mcpsctl           │   │
│  │  GitHub Action         │    │  SQLite (mcps, functions)     │   │
│  │                        │    │  Cache SHA-256                │   │
│  │  Templates (4×3)       │    │  Verify 15 checks             │   │
│  │  FSM Engine            │    │  Platdetect                   │   │
│  │  Hooks (5 categorias)  │    │  Event-driven dispatch        │   │
│  └────────┬───────────────┘    └──────────────────┬────────────┘   │
│           │                                       │                │
│           └──────────┐              ┌─────────────┘                │
│                      ▼              ▼                              │
│           ┌──────────────────────────────────────┐                 │
│           │         ADAPTER (bridge)              │                 │
│           │                                      │                 │
│           │  📍 mcps-as-objects/registry/src/adapter.py            │
│           │                                      │                 │
│           │  Responsabilidades:                  │                 │
│           │  ┌─────────────────────────────────┐ │                 │
│           │  │ 1. ingest(project_path)         │ │                 │
│           │  │    Lê blueprint.yaml            │ │                 │
│           │  │    Extrai: name, tools, sdk,    │ │                 │
│           │  │    pattern, hooks, platforms    │ │                 │
│           │  │    Gera mcp.json                │ │                 │
│           │  │    Gera server.py (FastMCP)     │ │                 │
│           │  │    Chama verify-mcp (15 checks) │ │                 │
│           │  │    Chama mcpsctl lock            │ │                 │
│           │  │    Chama register_mcp() no DB    │ │                 │
│           │  │                                 │ │                 │
│           │  │ 2. info(mcp_id)                 │ │                 │
│           │  │    Retorna info consolidada     │ │                 │
│           │  │    (blueprint + manifesto + FSM) │ │                 │
│           │  │                                 │ │                 │
│           │  │ 3. sync(mcp_id)                 │ │                 │
│           │  │    Atualiza se blueprint mudou   │ │                 │
│           │  │    Revalida, relock, re-registra │ │                 │
│           │  └─────────────────────────────────┘ │                 │
│           └──────────────────────────────────────┘                 │
│                                                                     │
│           ┌──────────────────────────────────────┐                 │
│           │  HOOK DE PÓS-SCAFFOLD (mcp-builder)  │                 │
│           │                                      │                 │
│           │  📍 mcps-as-objects/hooks/post-scaffold.ts             │
│           │                                      │                 │
│           │  Disparado após mcp-builder gerar    │                 │
│           │  um projeto:                         │                 │
│           │  1. Chama adapter.ingest()           │                 │
│           │  2. Se falhar → bloqueia (gate)      │                 │
│           │  3. Se ok → registra e notifica      │                 │
│           └──────────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ═══════════════════════════════════════════════════════════════════
## 4. COMPONENTES DO PLANO
## ═══════════════════════════════════════════════════════════════════

### 4.1 Adapter — `registry/src/adapter.py`

```python
"""
adapter.py — Bridge entre mcp-builder (blueprint.yaml) e mcps-as-objects (mcp.json).

Zero hardcoded: tudo lido de blueprint.yaml + schemas.
Agnóstico: funciona com Python, TS, Go, Rust — qualquer SDK/pattern.
Gerenciado: registra no DB, lockfile, verify.
"""

from pathlib import Path
from typing import Optional
from . import (
    db, crud, catalog, validator,
    constructor, verifier, snapshot
)

def ingest(
    project_path: str,
    platforms: Optional[list] = None,
    overwrite: bool = False
) -> dict:
    """
    Ingere um projeto gerado pelo mcp-builder no ecossistema.

    Fluxo:
    1. Lê blueprint.yaml (se existir) ou mcp.json
    2. Extrai: id, name, tools (viram functions), sdk, pattern, hooks
    3. Cria diretório em mcps/<id>/ com mcp.json + server.py
    4. Valida contra schema
    5. Executa verify-mcp (15 checks)
    6. Atualiza lockfile (SHA-256)
    7. Registra no SQLite
    8. Retorna resultado

    Zero hardcoded: inputs vêm do blueprint + parâmetros.
    Gerenciado: toda saída vai pro DB + lockfile.
    Agnóstico: blueprint.sdk define como gerar server.py.
    """
    ...

def info(mcp_id: str) -> dict:
    """
    Retorna info consolidada de um MCP gerido:
    - Manifesto (mcp.json)
    - Blueprint (se existir)
    - FSM states/transitions (se .mcp/state/ existir)
    - Hooks declarados
    - Runs recentes
    - Status do cache
    """
    ...

def sync(mcp_id: str) -> dict:
    """
    Sincroniza se o blueprint ou código mudou.
    Revalida, religa lockfile, re-registra.
    """
    ...
```

### 4.2 Template complementar no mcp-builder

O `mcp-builder` precisa gerar 2 arquivos extras em cada template:

**`mcp.json.hbs`** (contrato com mcps-as-objects):

```handlebars
{
  "id": "{{kebabCase name}}",
  "name": "{{name}}",
  "version": "0.1.0",
  "description": "{{description}}",
  "entry": "src/server.py",
  "runtime": {
    "language": "{{sdk}}",
    "image": "ubuntu-22.04",
    "estimated_duration_sec": 60
  },
  "functions": [
    {{#each tools}}
    {
      "name": "{{snakeCase name}}",
      "description": "{{description}}",
      "input_schema": {{{json inputSchema}}},
      "output_schema": {{{json outputSchema}}}
    }{{#unless @last}},{{/unless}}
    {{/each}}
  ],
  "platforms": ["*"],
  "pipeline": { "consumes": [], "produces": [] },
  "blueprint": {
    "sdk": "{{sdk}}",
    "pattern": "{{pattern}}",
    "hooks": {{{json hooks}}}
  }
}
```

**`src/server.py.hbs`** (FastMCP wrapper — para templates Python):

```handlebars
"""
{{description}}
MCP server gerado por mcp-builder → gerenciado por mcps-as-objects.
"""
from mcp.server.fastmcp import FastMCP
{{#if (eq sdk 'python')}}
from . import core
{{/if}}

mcp = FastMCP(name="{{kebabCase name}}")

{{#each tools}}
@mcp.tool()
def {{snakeCase name}}({{#each inputSchema.properties}}{{#if @key}}{{@key}}: {{type}}{{#unless @last}}, {{/unless}}{{/if}}{{/each}}) -> dict:
    """{{description}}"""{{#if (eq ../sdk 'python')}}
    return core.{{snakeCase name}}({{#each inputSchema.properties}}{{#if @key}}{{@key}}={{@key}}{{#unless @last}}, {{/unless}}{{/if}}{{/each}}){{/if}}
{{/each}}

if __name__ == "__main__":
    mcp.run()
```

### 4.3 Hook pós-scaffold — `hooks/post-scaffold.ts`

```typescript
/**
 * post-scaffold.ts — Hook de integração mcp-builder ↔ mcps-as-objects
 *
 * Categoria: event (disparado após scaffold bem-sucedido)
 * Função: chama adapter.ingest() para registrar o MCP no ecossistema
 *
 * Zero hardcoded: caminhos vêm do HookContext.
 * Gerenciado: se ingest falhar, hook bloqueia.
 */

import { Hook } from '../builder/src/types';

export const postScaffoldHook: Hook = async (ctx, payload) => {
  const { projectPath } = payload as { projectPath: string };
  const { logger } = ctx;

  try {
    // Chama o adapter Python via subprocess JSON
    const result = await execPythonAdapter('ingest', {
      project_path: projectPath,
      platforms: ['*'],
    });

    if (!result.ok) {
      return {
        ok: false,
        block: {
          reason: `Adapter rejeitou o MCP: ${result.error}`,
          suggestions: [
            'Verifique blueprint.yaml',
            'Execute adapter.ingest() manualmente para ver erros',
          ],
        },
      };
    }

    logger.info(`MCP registrado: ${result.mcp_id}`);
    return { ok: true, artifacts: result.artifacts };
  } catch (err) {
    return {
      ok: false,
      block: {
        reason: `Falha no adapter: ${err.message}`,
        suggestions: ['Verifique se mcps-as-objects está acessível'],
      },
    };
  }
};
```

---

## ═══════════════════════════════════════════════════════════════════
## 5. FLUXO COMPLETO (passo a passo)
## ═══════════════════════════════════════════════════════════════════

### 5.1 Criar e Gerenciar um MCP (ciclo completo)

```
PASSO 1: mcp-builder new
──────────────────────────
$ npx mcp-builder new sentiment-analyzer \
    --sdk python --pattern factory

  ├─ Gera: mcps/sentiment-analyzer/
  │   ├─ blueprint.yaml
  │   ├─ mcp.json                  ← NOVO (contrato)
  │   ├─ src/server.py             ← NOVO (FastMCP wrapper)
  │   ├─ src/*.py                  ← lógica do template factory
  │   ├─ tests/
  │   ├─ .mcp/state/               ← FSM
  │   └─ .github/workflows/        ← CI/CD
  │
  └─ Hook pós-scaffold dispara:

PASSO 2: adapter.ingest (automático via hook)
───────────────────────────────────────────────
  $ python3 -m registry.src.adapter ingest \
      --from mcps/sentiment-analyzer

  ├─ Lê blueprint.yaml
  │   ├─ name: sentiment-analyzer
  │   ├─ sdk: python
  │   ├─ pattern: factory
  │   ├─ tools: [analyze, train, evaluate]
  │   └─ hooks: [cost-limit, rate-limit]
  │
  ├─ Valida mcp.json contra schema
  ├─ verify-mcp sentiment-analyzer
  │   ├─ 📁 Estrutura ✅
  │   ├─ 📜 Schema ✅
  │   ├─ 🔧 Tools condizentes ✅
  │   ├─ 🧪 Testes existem ✅
  │   └─ 15 checks → 0 erros ✅
  │
  ├─ mcpsctl lock
  │   └─ SHA-256: a1b2c3... → cache key
  │
  └─ register no SQLite
      ├─ mcps: id, name, version, manifest_hash
      ├─ functions: analyze, train, evaluate
      └─ runs: (vazio — primeiro run ainda não aconteceu)

PASSO 3: Gerenciar (mcps-as-objects)
─────────────────────────────────────
  $ curl http://localhost:8712/mcps/sentiment-analyzer
  → { id, name, functions, ..., blueprint: { sdk, pattern, hooks } }

  $ curl -X POST http://localhost:8712/mcps/sentiment-analyzer/dispatch
  → { run_id, status: "dispatched" }

  $ gh workflow run mcp-runtime.yml -f mcp_id=sentiment-analyzer
  → Executa SOMENTE sentiment-analyzer com FSM:
      draft → testing → staging → release
      Hooks: cost-limit ✅, rate-limit ✅
```

### 5.2 Zero Hardcoded — Evidência

```
BLUEPRINT.YAML (fonte):          MCP.JSON (gerado):
─────────────────────            ───────────────────
name: sentiment-analyzer         id: sentiment-analyzer
sdk: python                      runtime.language: python
pattern: factory                 
tools:                           functions:
  - name: analyze                  - name: analyze
    inputSchema: {}                  input_schema: {}
  - name: train                    - name: train
    inputSchema: {}                  input_schema: {}

NENHUM valor fixo em adapter.py.  Tudo lido do blueprint + schemas.
Adapter.py NÃO contém:
  ❌ "sentiment-analyzer" — hardcoded ❌
  ❌ "python" — hardcoded ❌
  ❌ "factory" — hardcoded ❌
  ✅ blueprint.yaml → adapter → DB
```

---

## ═══════════════════════════════════════════════════════════════════
## 6. MCPs DA INTEGRAÇÃO (objetos gerenciados)
## ═══════════════════════════════════════════════════════════════════

Cada **componente da integração** vira um MCP gerenciado:

| MCP | Função | Local/Remoto | Depende de |
|-----|--------|-------------|------------|
| `mcp-builder` | Scaffold de MCPs (CLI/server/API) | **Local** | blueprint.yaml |
| `mcps-as-objects` | Registry, DB, API, cache, verify | **Local** | SQLite, schemas |
| `adapter-bridge` | Ponte entre builder e registry | **Local** | mcp-builder + mcps-as-objects |
| `verify-mcp` | 15 checks de conformidade | **Local** | schemas/ |
| `fsm-engine` | Máquina de estados GitOps | **Local** | .mcp/state/ |
| `hook-system` | Gate/trigger/event/monitor/advisor | **Local+Remoto** | hooks/ |
| `template-engine` | Geração de templates (4 SDKs × 3) | **Local** | templates/ |

**Cada um desses MCPs segue o padrão:** `mcp.json`, `src/core.py`, `src/server.py`, `tests/`, lockfile, verify.

---

## ═══════════════════════════════════════════════════════════════════
## 7. FASES DE IMPLEMENTAÇÃO
## ═══════════════════════════════════════════════════════════════════

### Fase 1 — Adapter Core (bridge mínimo)

```
Duração: ~2 sessões
Entrega: adapter.ingest() funcional

Arquivos:
  registry/src/adapter.py         ← core bridge
  registry/tests/test_adapter.py  ← testes do adapter
  schemas/adapter.schema.json     ← contrato adapter (opcional)

MCPs envolvidos:
  ✅ mcps-as-objects (registry)
  ⏳ mcp-builder (precisa esperar)
```

### Fase 2 — Templates Complementares

```
Duração: ~2 sessões
Entrega: mcp-builder gera mcp.json + server.py

Arquivos (no mcp-builder):
  templates/*/mcp.json.hbs        ← novo template
  templates/*/src/server.py.hbs   ← novo template

MCPs envolvidos:
  ✅ mcp-builder
```

### Fase 3 — Hook pós-scaffold

```
Duração: ~1 sessão
Entrega: mcp-builder chama adapter automaticamente

Arquivos (no mcp-builder):
  hooks/post-scaffold.ts          ← hook de integração

MCPs envolvidos:
  ✅ mcp-builder
  ✅ adapter-bridge
```

### Fase 4 — FSM + Blueprint + Registry (unificação)

```
Duração: ~3 sessões
Entrega: Registry mostra FSM, blueprints, hooks

Arquivos (no mcps-as-objects):
  registry/src/fsm.py             ← leitor de states.yaml
  registry/src/blueprint.py       ← leitor de blueprint.yaml
  registry/src/api.py             ← novos endpoints

MCPs envolvidos:
  ✅ mcps-as-objects
  ✅ fsm-engine
  ✅ template-engine
```

### Fase 5 — Hooks de Governança (cross-platform)

```
Duração: ~2 sessões
Entrega: 5 hooks do mcp-builder disponíveis no registry

Arquivos:
  hooks/ → (copiados do mcp-builder)
  registry/src/hooks/ → adapters Python para cada hook

MCPs envolvidos:
  ✅ hook-system
  ✅ mcps-as-objects
```

---

## ═══════════════════════════════════════════════════════════════════
## 8. GARANTIAS DE COMPLIANCE (checklist)
## ═══════════════════════════════════════════════════════════════════

### 8.1 Zero Hardcoded

```
□ adapter.py não contém nomes de MCP fixos
□ adapter.py não contém SDKs/patterns fixos
□ adapter.py lê tudo de blueprint.yaml
□ adapter.py usa schemas/ para validar saída
□ server.py.hbs usa Handlebars (não string concatenada)
□ mcp.json.hbs usa Handlebars (não string concatenada)
```

### 8.2 100% Gerenciado

```
□ adapter.ingest() chama register_mcp() no DB
□ adapter.ingest() chama mcpsctl lock
□ adapter.ingest() chama verify-mcp
□ adapter.ingest() retorna erro se verify falhar
□ adapter.sync() atualiza lockfile + DB se blueprint mudar
□ adapter.info() retorna dados consolidados (manifesto + FSM + runs)
```

### 8.3 Agnóstico

```
□ adapter funciona com Python, TS, Go, Rust
□ adapter funciona com stateless, event, factory
□ adapter funciona com qualquer hook declarado
□ adapter funciona em Termux, GitHub Actions, dev local
□ adapter detecta SDK do blueprint e gera server.py adequado
```

### 8.4 Replicável

```
□ Mesmo blueprint.yaml + mesmo adapter → mesmo mcp.json
□ Cache key inclui SHA-256 do blueprint + manifesto
□ FSM é determinística (states.yaml + transitions.yaml versionados)
□ Testes do adapter rodam em CI (mcp-verify.yml)
□ Dockerfile opcional para ambiente replicável
```

---

## ═══════════════════════════════════════════════════════════════════
## 9. MÉTRICAS DE SUCESSO
## ═══════════════════════════════════════════════════════════════════

| Métrica | Atual | Alvo pós-integração |
|---------|-------|---------------------|
| MCPs gerenciados | 4 (só Python) | Ilimitado (4 SDKs × 3 padrões) |
| Templates disponíveis | 1 (`_template/`) | 13 (1 + 12 do mcp-builder) |
| Cobertura de escopo | 40%+40% = 80% | **~98%** |
| Testes | 27 (registry) + 161 (builder) | **188** (ambos + adapter) |
| Hooks de governança | 0 | **5** (cost-limit, rate-limit, audit-log, dep-vulns, prompt-injection) |
| FSM implementada | workflow linear | **6 estados** (draft→testing→staging→release + fail, error) |
| Zero hardcoded compliance | Parcial | **100%** (verificado por teste de lint) |
| Tempo para criar + gerenciar MCP | ~2min manual | **~5s** (mcp-builder + hook + adapter) |

---

## ═══════════════════════════════════════════════════════════════════
## 10. PRÓXIMOS PASSOS (ação imediata)
## ═══════════════════════════════════════════════════════════════════

| Passo | Ação | Responsável |
|-------|------|-------------|
| **1** | Revisar este plano e aprovar | Você |
| **2** | Iniciar Fase 1 — adapter.py | Eu implemento |
| **3** | Testar adapter com example-greeter (prova real) | Eu + você |
| **4** | Iniciar Fase 2 — templates complementares no mcp-builder | Eu implemento |
| **5** | Integrar via PR na branch `feat/pi-ecosystem-management` | GitOps |

**Aguardando sua ordem para iniciar a implementação da Fase 1.** 🚀
