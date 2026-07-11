# 🏗️ Plano de Integração: mcp-builder → mcps-as-objects

> **Bridge + Adapter + Compliance — Zero Hardcoded, 100% Gerenciado, Agnóstico, Replicável.**
> **Gerenciado como GitHub Project (Kanban event-driven).**

---

## ═══════════════════════════════════════════════════════════════════
## 0. GESTÃO DO PROJETO — KANBAN EVENT-DRIVEN
## ═══════════════════════════════════════════════════════════════════

### 0.1 GitHub Project (Kanban)

```
Board: Integração mcp-builder ↔ mcps-as-objects

┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│   📋     │   │   🏗️    │   │   ✅     │   │   🚀     │   │   📦     │
│ Backlog  │──▶│ Doing    │──▶│ Review   │──▶│ Staging  │──▶│ Done     │
│          │   │          │   │          │   │          │   │          │
│ Issues   │   │ Em       │   │ PR       │   │ Testado  │   │ Fechado  │
│ prioriz. │   │ execução │   │ aberto   │   │ em CI    │   │ entregue │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
      │              │              │              │              │
      └──────────────┴────── Eventos ──────────────┴──────────────┘
                          │
                    ┌─────▼──────┐
                    │ Workflows  │
                    │ GitHub     │
                    │ Actions    │
                    │ · Issue →  │
                    │   Board    │
                    │ · PR →     │
                    │   Review   │
                    │ · Merge →  │
                    │   Done     │
                    └────────────┘
```

### 0.2 Labels (Tags)

| Label | Cor | Significado |
|-------|-----|-------------|
| `fase-1-adapter` | 🔵 | Adapter core |
| `fase-2-templates` | 🟢 | Templates complementares |
| `fase-3-hooks` | 🟠 | Hook pós-scaffold |
| `fase-4-fsm` | 🟣 | FSM + Blueprint + Registry |
| `fase-5-governanca` | 🔴 | Hooks de governança |
| `compliance` | 🟡 | Zero hardcoded / gerenciado / agnóstico |
| `bug` | 🔴 | Erro |
| `test` | 🟢 | Testes |
| `docs` | 🔵 | Documentação |

### 0.3 Milestones

| Milestone | Previsão | Entregas |
|-----------|----------|----------|
| **M1 — Bridge Funcional** | Fase 1+2 | `adapter.ingest()` + templates |
| **M2 — Integração Automática** | Fase 3 | Hook pós-scaffold |
| **M3 — Unificação** | Fase 4 | FSM + Blueprint + Registry |
| **M4 — Governança** | Fase 5 | Hooks cross-platform |

### 0.4 Workflow Event-Driven do Próprio Projeto

```yaml
# .github/workflows/project-automation.yml
# Auto-gerencia o Kanban baseado em eventos

on:
  issues:
    types: [opened, labeled, closed]
  pull_request:
    types: [opened, ready_for_review, closed]

jobs:
  move-cards:
    runs-on: ubuntu-22.04
    steps:
      - name: Issue aberta → Backlog
        if: github.event_name == 'issues' && github.event.action == 'opened'
        run: gh project item-add --project "Integração" --column "Backlog" $ISSUE

      - name: Issue com label → Doing
        if: github.event_name == 'issues' && github.event.action == 'labeled'
        run: gh project item-move --project "Integração" --column "Doing" $ISSUE

      - name: PR aberto → Review
        if: github.event_name == 'pull_request' && github.event.action == 'opened'
        run: gh project item-move --project "Integração" --column "Review" $PR

      - name: PR merged → Done
        if: github.event_name == 'pull_request' && github.event.action == 'closed' && github.event.pull_request.merged
        run: gh project item-move --project "Integração" --column "Done" $PR
```

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
## 4. TASKLIST — FLASHCARDS COM CRITÉRIOS DE VALIDAÇÃO
## ═══════════════════════════════════════════════════════════════════

Cada card vira uma **Issue no GitHub** com template padronizado.

### 📌 Template de Issue

```markdown
---
title: "[FASE-X] Nome da tarefa"
labels: [fase-x, tipo]
assignees: camillanapoles
project: Integração mcp-builder ↔ mcps-as-objects
milestone: M1 — Bridge Funcional
---

## Descrição
<!-- O que precisa ser feito -->

## Critérios de Validação
<!-- [ ] = check automático no CI -->
- [ ] Código implementado
- [ ] Testes passando (pytest)
- [ ] verify-mcp 15 checks passando
- [ ] Lockfile atualizado
- [ ] PR aprovado e merged
- [ ] CI verde (mcp-validate + mcp-verify)

## Compliance
- [ ] Zero hardcoded (sem string fixa do nome do MCP)
- [ ] Gerenciado (DB + lockfile + verify)
- [ ] Agnóstico (não depende de SDK específico)
- [ ] Testado (testes no adapter + verify)

## Dependências
<!-- #issue se aplicável -->

## Notas
```

---

### 🃏 Card 1.1 — adapter.py: `ingest()` core

```
ID: #1
Título: [FASE-1] adapter.ingest() — ler blueprint.yaml e gerar mcp.json
Labels: fase-1-adapter, compliance
Milestone: M1
Esforço: M
```

**Implementação:**

```python
# registry/src/adapter.py
def ingest(project_path: str, platforms: Optional[list] = None) -> dict:
    """
    1. Lê blueprint.yaml do projeto gerado pelo mcp-builder
    2. Extrai: name, tools → functions, sdk, pattern, hooks
    3. Gera mcps/<id>/mcp.json (válido contra schema)
    4. Chama verify-mcp (15 checks)
    5. Chama mcpsctl lock (SHA-256)
    6. Chama register_mcp() (SQLite)
    7. Retorna {mcp_id, status, manifest_hash, run_id}
    """
```

**Validação:**

- [ ] `adapter.ingest("mcps/example-greeter")` → mcp.json gerado identico ao original
- [ ] `adapter.ingest("mcps/example-greeter")` → verify-mcp passa (0 erros)
- [ ] `adapter.ingest("mcps/example-greeter")` → lockfile atualizado
- [ ] `adapter.ingest("mcps/example-greeter")` → DB tem o MCP registrado
- [ ] Zero hardcoded: blueprint.yaml é a única fonte

---

### 🃏 Card 1.2 — adapter.py: `info()` e `sync()`

```
ID: #2
Título: [FASE-1] adapter.info() e adapter.sync() — consulta e atualização
Labels: fase-1-adapter
Milestone: M1
Esforço: P
```

**Validação:**

- [ ] `adapter.info("example-greeter")` → retorna manifesto + FSM + runs
- [ ] `adapter.sync("example-greeter")` → se blueprint mudou, revalida, relock, re-registra
- [ ] Se nada mudou, sync é no-op
- [ ] Se algo mudou e quebrou verify, sync retorna erro

---

### 🃏 Card 1.3 — Testes do adapter

```
ID: #3
Título: [FASE-1] Testes do adapter (unit + integration)
Labels: fase-1-adapter, test
Milestone: M1
Esforço: G
```

**Arquivo:** `registry/tests/test_adapter.py`

**Validação:**

- [ ] `test_ingest_example_greeter()` — ingest do example-greeter existente
- [ ] `test_ingest_novo_mcp()` — ingest de um blueprint.yaml novo
- [ ] `test_ingest_sem_blueprint()` — fallback se não tem blueprint.yaml
- [ ] `test_ingest_sdk_python()` — SDK Python
- [ ] `test_ingest_sdk_typescript()` — SDK TypeScript
- [ ] `test_ingest_sdk_go()` — SDK Go
- [ ] `test_ingest_sdk_rust()` — SDK Rust
- [ ] `test_ingest_pattern_stateless()` — pattern stateless
- [ ] `test_ingest_pattern_event()` — pattern event
- [ ] `test_ingest_pattern_factory()` — pattern factory
- [ ] `test_info()` — info retorna dados corretos
- [ ] `test_sync_sem_mudanca()` — sync é no-op
- [ ] `test_sync_com_mudanca()` — sync reage a mudança
- [ ] `test_sync_quebra_verify()` — sync bloqueia se verify falha
- [ ] Zero hardcoded: nenhum nome de MCP fixo nos testes (usa parametrize)

---

### 🃏 Card 2.1 — Template `mcp.json.hbs`

```
ID: #4
Título: [FASE-2] Template mcp.json.hbs no mcp-builder (4 SDKs × 3 patterns)
Labels: fase-2-templates
Milestone: M1
Esforço: M
```

**12 arquivos a criar/alterar:**

```
templates/python-sdk/stateless/mcp.json.hbs
templates/python-sdk/event/mcp.json.hbs
templates/python-sdk/factory/mcp.json.hbs
templates/typescript-sdk/stateless/mcp.json.hbs
templates/typescript-sdk/event/mcp.json.hbs
templates/typescript-sdk/factory/mcp.json.hbs
templates/go-sdk/stateless/mcp.json.hbs
templates/go-sdk/event/mcp.json.hbs
templates/go-sdk/factory/mcp.json.hbs
templates/rust-sdk/stateless/mcp.json.hbs
templates/rust-sdk/event/mcp.json.hbs
templates/rust-sdk/factory/mcp.json.hbs
```

**Validação:**

- [ ] `npx mcp-builder new x --sdk python --pattern stateless` → gera `mcp.json`
- [ ] `npx mcp-builder new x --sdk python --pattern event` → gera `mcp.json`
- [ ] `npx mcp-builder new x --sdk python --pattern factory` → gera `mcp.json`
- [ ] Idem para TypeScript, Go, Rust
- [ ] `mcp.json` gerado é válido contra `schemas/mcp-manifest.schema.json`
- [ ] `mcp.json` gerado tem `blueprint.sdk` e `blueprint.pattern` corretos
- [ ] `mcp.json` gerado tem `functions` convertidas de `tools`

---

### 🃏 Card 2.2 — Template `src/server.py.hbs` (Python)

```
ID: #5
Título: [FASE-2] Template server.py.hbs (FastMCP wrapper Python)
Labels: fase-2-templates
Milestone: M1
Esforço: M
```

**Validação:**

- [ ] Gera `src/server.py` com `FastMCP(name=...)`
- [ ] Gera `@mcp.tool()` para cada tool declarada
- [ ] Importa de `core` (lógica pura)
- [ ] `verify-mcp` passa (tools condizentes com manifesto)
- [ ] `python src/server.py` inicia sem erro

---

### 🃏 Card 3.1 — Hook pós-scaffold

```
ID: #6
Título: [FASE-3] Hook post-scaffold — chama adapter.ingest automaticamente
Labels: fase-3-hooks
Milestone: M2
Esforço: G
```

**Validação:**

- [ ] `mcp-builder new x` → hook dispara automaticamente
- [ ] Hook chama `adapter.ingest()` com o path do projeto gerado
- [ ] Se adapter retorna ok → hook retorna ok
- [ ] Se adapter retorna erro → hook bloqueia (gate)
- [ ] Mensagem de erro contém sugestões de correção

---

### 🃏 Card 4.1 — FSM no Registry

```
ID: #7
Título: [FASE-4] FSM Engine integrada ao Registry (ler .mcp/state/)
Labels: fase-4-fsm
Milestone: M3
Esforço: G
```

**Validação:**

- [ ] `GET /mcps/{id}/fsm` → retorna estados + transições do `.mcp/state/`
- [ ] `GET /mcps/{id}/fsm/current` → estado atual (do DB runs)
- [ ] `GET /mcps/{id}/fsm/mermaid` → diagrama Mermaid
- [ ] Registry mostra FSM de MCPs gerados pelo mcp-builder

---

### 🃏 Card 4.2 — Blueprint no Registry

```
ID: #8
Título: [FASE-4] Blueprint exposto no Registry (ler blueprint.yaml)
Labels: fase-4-fsm
Milestone: M3
Esforço: M
```

**Validação:**

- [ ] `GET /mcps/{id}/blueprint` → retorna blueprint.yaml parseado
- [ ] Blueprint fica visível no `mcpsctl describe <id>`
- [ ] Se não tem blueprint, retorna 404 com mensagem clara

---

### 🃏 Card 5.1 — 5 Hooks de Governança

```
ID: #9
Título: [FASE-5] 5 hooks de governança disponíveis no Registry
Labels: fase-5-governanca, compliance
Milestone: M4
Esforço: GG
```

**Hooks a portar do mcp-builder:**

| Hook | Categoria | Função |
|------|-----------|--------|
| `cost-limit` | gate | Bloqueia se custo LLM exceder orçamento |
| `rate-limit` | gate | Rate limiter sliding window |
| `audit-log` | monitor | Append-only log + webhook |
| `dependency-vulns` | advisor | Bloqueia release com vulns |
| `prompt-injection-detector` | gate | Detecta 7 padrões de injection |

**Validação:**

- [ ] Cada hook tem versão Python (para executar local)
- [ ] Cada hook tem versão TS (para executar em workflow)
- [ ] `POST /mcps/{id}/hooks/run?hook=rate-limit` → executa hook
- [ ] `POST /mcps/{id}/hooks/run?hook=cost-limit` → bloqueia se excedido
- [ ] Testes unitários para cada hook (mínimo 5 testes por hook)
- [ ] Documentação de cada hook

---

### 🃏 Card 5.2 — Workflow de Projeto (GitHub Project Automation)

```
ID: #10
Título: [FASE-5] Workflow de automação do Kanban (project-automation.yml)
Labels: fase-5-governanca
Milestone: M4
Esforço: P
```

**Validação:**

- [ ] Issue aberta → card vai para Backlog
- [ ] Issue com label → card vai para Doing
- [ ] PR aberto → card vai para Review
- [ ] PR merged → card vai para Done
- [ ] Tudo via GitHub Actions (event-driven)

---

## ═══════════════════════════════════════════════════════════════════
## 5. WORKFLOWS DO PRÓPRIO PROJETO (EVENT-DRIVEN)
## ═══════════════════════════════════════════════════════════════════

### 5.1 Automação do Kanban

```yaml
# .github/workflows/project-automation.yml
name: Project Automation
on:
  issues:
    types: [opened, labeled, closed]
  pull_request:
    types: [opened, ready_for_review, closed]

jobs:
  automate:
    runs-on: ubuntu-22.04
    steps:
      - name: Issue opened → Backlog
        uses: actions/github-script@v7
        if: github.event_name == 'issues' && github.event.action == 'opened'
        with:
          script: |
            await github.rest.projects.createCard({
              column_id: COLUMN_BACKLOG,
              content_id: context.payload.issue.id,
              content_type: 'Issue'
            })
```

### 5.2 CI por Card (validação automática)

```yaml
# .github/workflows/card-validate.yml
# Dispara quando card move para "Review"
name: Card Validate
on:
  project_card:
    types: [moved]

jobs:
  validate:
    if: github.event.changes.column_id == COLUMN_REVIEW
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4
      - name: Rodar verify-mcp
        run: python3 scripts/verify-mcp.py --all
      - name: Rodar testes do adapter
        run: python3 -m pytest registry/tests/test_adapter.py -v
```

---

## ═══════════════════════════════════════════════════════════════════
## 6. FLUXO COMPLETO (passo a passo)
## ═══════════════════════════════════════════════════════════════════

### 6.1 Criar e Gerenciar um MCP

```
PASSO 1: mcp-builder new
──────────────────────────
$ npx mcp-builder new sentiment-analyzer \
    --sdk python --pattern factory

  ├─ Gera: mcps/sentiment-analyzer/
  │   ├─ blueprint.yaml
  │   ├─ mcp.json                  ← NOVO (contrato)
  │   ├─ src/server.py             ← NOVO (FastMCP wrapper)
  │   ├─ src/*.py                  ← lógica
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
  ├─ Valida mcp.json contra schema
  ├─ verify-mcp → 0 erros
  ├─ mcpsctl lock → SHA-256
  └─ register no SQLite

PASSO 3: Gerenciar (mcps-as-objects)
─────────────────────────────────────
  $ curl http://localhost:8712/mcps/sentiment-analyzer
  $ curl -X POST http://localhost:8712/mcps/sentiment-analyzer/dispatch
```

### 6.2 Ciclo de Desenvolvimento da Própria Integração

```
1. Criar Issue com template de card
   → Workflow move para "Backlog"

2. Iniciar desenvolvimento
   → Label fase-X → workflow move para "Doing"

3. Abrir PR com implementação
   → Workflow move para "Review"
   → CI roda testes + verify-mcp

4. Aprovar e mergear PR
   → Workflow move para "Done"
   → Card fecha automaticamente
```

---

## ═══════════════════════════════════════════════════════════════════
## 7. FASES DE IMPLEMENTAÇÃO (com milestones e cards)
## ═══════════════════════════════════════════════════════════════════

```
MILESTONE M1 — BRIDGE FUNCIONAL
├── 🃏 Card 1.1 — adapter.ingest() core
├── 🃏 Card 1.2 — adapter.info() e adapter.sync()
├── 🃏 Card 1.3 — Testes do adapter (15 testes)
├── 🃏 Card 2.1 — Template mcp.json.hbs (12 arquivos)
└── 🃏 Card 2.2 — Template server.py.hbs (Python)

MILESTONE M2 — INTEGRAÇÃO AUTOMÁTICA
├── 🃏 Card 3.1 — Hook post-scaffold
└── 🃏 Card 2.2 — (continuação)

MILESTONE M3 — UNIFICAÇÃO
├── 🃏 Card 4.1 — FSM Engine no Registry
└── 🃏 Card 4.2 — Blueprint no Registry

MILESTONE M4 — GOVERNANÇA
├── 🃏 Card 5.1 — 5 hooks de governança
├── 🃏 Card 5.2 — Workflow de automação do Kanban
└── 🃏 Card 5.3 — Documentação final
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
□ Testes usam parametrize, não nomes fixos
```

### 8.2 100% Gerenciado

```
□ adapter.ingest() chama register_mcp() no DB
□ adapter.ingest() chama mcpsctl lock
□ adapter.ingest() chama verify-mcp
□ adapter.ingest() retorna erro se verify falhar
□ adapter.sync() atualiza lockfile + DB se blueprint mudar
□ adapter.info() retorna dados consolidados
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
```

---

## ═══════════════════════════════════════════════════════════════════
## 9. MÉTRICAS DE SUCESSO
## ═══════════════════════════════════════════════════════════════════

| Métrica | Atual | Alvo pós-integração | Verificado por |
|---------|-------|---------------------|----------------|
| MCPs gerenciados | 4 (só Python) | Ilimitado (4 SDKs × 3 padrões) | `GET /mcps` |
| Templates disponíveis | 1 (`_template/`) | 13 (1 + 12 do mcp-builder) | `ls templates/` |
| Cobertura de escopo | 40%+40% = 80% | **~98%** | checklist compliance |
| Testes do adapter | 0 | **15** | `pytest registry/tests/test_adapter.py` |
| Hooks de governança | 0 | **5** | `POST /mcps/{id}/hooks/run?hook=...` |
| FSM implementada | workflow linear | **6 estados** | `GET /mcps/{id}/fsm` |
| Zero hardcoded | Parcial | **100%** | teste de lint no CI |
| Tempo criar + gerenciar MCP | ~2min manual | **~5s** | `mcp-builder new + hook` |
| Cards no Kanban | 0 | **10** | GitHub Project |
| Workflows de automação | 0 | **3** | `.github/workflows/project-*.yml` |

---

## ═══════════════════════════════════════════════════════════════════
## 10. CRIAÇÃO DAS ISSUES (próxima ação)
## ═══════════════════════════════════════════════════════════════════

Após aprovação deste plano, o próximo passo é:

1. Criar **GitHub Project** "Integração mcp-builder ↔ mcps-as-objects" (Kanban)
2. Abrir **10 Issues** (uma por card) com labels e milestones
3. Configurar **3 workflows** de automação do projeto
4. Iniciar **Card 1.1** — implementação do `adapter.ingest()`

```bash
# Comandos para criar o Project e Issues via CLI:
gh project create "Integração mcp-builder ↔ mcps-as-objects" --org camillanapoles
gh issue create --title "[FASE-1] adapter.ingest()" --label fase-1-adapter
gh issue create --title "[FASE-1] adapter.info() e adapter.sync()" --label fase-1-adapter
# ... etc
```

---

**Aguardando sua ordem para:**
1. ✅ Aprovar o plano revisado
2. 🔧 Criar o GitHub Project + Issues + Workflows
3. 🚀 Iniciar implementação do Card 1.1
