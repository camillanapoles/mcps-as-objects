# 🏗️ MCP-MANAGER — Plano de Integração

> **Unificação de `mcp-builder` + `mcps-as-objects` em um único ecossistema gerenciado.**

---

## ═══════════════════════════════════════════════════════════════════
## 0. CONCEITO
## ═══════════════════════════════════════════════════════════════════

```
MCP-MANAGER = mcp-builder (CRIA) + bridge (ADAPTER) + mcps-as-objects (GERENCIA)
```

```
┌─────────────────────────────────────────────────────────────────────┐
│                         MCP-MANAGER                                  │
│                                                                     │
│  ┌──────────────────┐   ┌──────────────────┐   ┌────────────────┐  │
│  │  mcp-builder     │   │  ADAPTER (bridge) │   │ mcps-as-objects│  │
│  │                  │   │                  │   │                │  │
│  │  CLI / MCP       │──▶│  blueprint.yaml  │──▶│  Registry API  │  │
│  │  HTTP / Action   │   │  → mcp.json      │   │  SQLite DB     │  │
│  │                  │   │  → server.py     │   │  Cache SHA-256 │  │
│  │  4 SDKs × 3     │   │  → verify-mcp    │   │  Verify 15     │  │
│  │  FSM + Hooks    │   │  → lock + DB     │   │  Event-driven  │  │
│  │  161 testes     │   │                  │   │  Plataforma    │  │
│  └──────────────────┘   └──────────────────┘   └────────────────┘  │
│                                                                     │
│  FLUXO: mcp-builder new → adapter ingest → registry gerencia       │
│                                                                     │
│  ESCOPO TOTAL: ~95%                                                 │
│  COBERTURA: CRIA (40%) + BRIDGE (5%) + GERENCIA (50%) = 95%        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ═══════════════════════════════════════════════════════════════════
## 1. ESTRUTURA DO PROJETO (pós-integração)
## ═══════════════════════════════════════════════════════════════════

```
MCP-MANAGER/
│
├── mcp-builder/                    # ← NOVO (submódulo ou diretório)
│   ├── builder/src/                #   TS core (CLI, MCP, HTTP, Action)
│   ├── hooks/                      #   Hooks system
│   ├── templates/                  #   4 SDKs × 3 patterns
│   ├── .mcp/state/                 #   FSM (states.yaml, transitions.yaml)
│   ├── docs/                       #   Documentação do builder
│   ├── tests/                      #   161 testes
│   └── package.json
│
├── mcps/                           # MCPs gerenciados (output do builder + registry)
│   ├── _template/
│   ├── example-greeter/
│   ├── python-termux-builder/
│   └── ...
│
├── registry/                       # Gestão (já existe)
│   ├── src/
│   │   ├── api.py
│   │   ├── server.py
│   │   ├── adapter.py              # ← NOVO (bridge)
│   │   ├── db.py / crud.py / ...
│   │   └── ...
│   └── tests/
│       └── test_adapter.py         # ← NOVO (15 testes)
│
├── schemas/                        # Contratos
│   └── mcp-manifest.schema.json
│
├── scripts/
│   └── verify-mcp.py
│
├── .github/workflows/
│   ├── mcp-runtime.yml
│   ├── project-automation.yml      # ← NOVO (automação do Kanban)
│   └── card-validate.yml           # ← NOVO (validação por card)
│
├── docs/
│   ├── INTEGRATION-PLAN.md
│   └── ...
│
├── mcps-lock.json
├── EXECUTION-CHECKLIST.md
└── README.md
```

---

## ═══════════════════════════════════════════════════════════════════
## 2. ETAPAS (STAGES) — visão geral
## ═══════════════════════════════════════════════════════════════════

```
ETAPA 0: Fundação (GitHub Project + Issues + Workflows)
         ├── 0.1 Criar GitHub Project (Kanban)
         ├── 0.2 Criar Labels + Milestones
         ├── 0.3 Abrir 10 Issues (cards)
         └── 0.4 Workflows de automação

ETAPA 1: Bridge Core (adapter.py)
         ├── 1.1 adapter.ingest() — core
         ├── 1.2 adapter.info() + adapter.sync()
         └── 1.3 Testes do adapter (15 testes)

ETAPA 2: Templates Complementares (mcp-builder)
         ├── 2.1 mcp.json.hbs (12 arquivos)
         └── 2.2 server.py.hbs (FastMCP wrapper)

ETAPA 3: Automação do Fluxo
         ├── 3.1 Hook pós-scaffold (chama adapter)
         └── 3.2 CI/CD: builder → registry register

ETAPA 4: Unificação FSM + Blueprint
         ├── 4.1 FSM no Registry (ler .mcp/state/)
         └── 4.2 Blueprint no Registry (ler blueprint.yaml)

ETAPA 5: Governança Cross-Platform
         ├── 5.1 5 hooks de governança (cost-limit, rate-limit, audit-log, dep-vulns, prompt-injection)
         └── 5.2 Documentação final
```

---

## ═══════════════════════════════════════════════════════════════════
## 3. TASKS POR ETAPA (com validação e GitHub Issues)
## ═══════════════════════════════════════════════════════════════════

### ETAPA 0 — Fundação

```
🎯 Objetivo: Preparar o ambiente de desenvolvimento gerenciado via GitHub Project.
📦 Entrega: Kanban configurado, 10 Issues abertas, workflows de automação rodando.
```

| # | Task | Descrição | Validação | Issue |
|---|------|-----------|-----------|-------|
| 0.1 | Criar GitHub Project | Board "MCP-MANAGER" com 5 colunas | Board visível em github.com/projects | — |
| 0.2 | Criar Labels + Milestones | 9 labels (fase-1 a fase-5, compliance, bug, test, docs) + 5 milestones (M0 a M4) | Labels e milestones listáveis via `gh label list` | — |
| 0.3 | Abrir 10 Issues | Uma issue por card com template (título, labels, milestone, checklist) | 10 issues abertas, cada uma com body contendo critérios de validação | #1 a #10 |
| 0.4 | Workflows de automação | `project-automation.yml` (move cards por evento) + `card-validate.yml` (valida ao mover) | Issue aberta → Backlog. Label → Doing. PR → Review. Merge → Done | #10 |

---

### ETAPA 1 — Bridge Core

```
🎯 Objetivo: adapter.py que lê blueprint.yaml do mcp-builder e gera mcp.json + registra no ecossistema.
📦 Entrega: adapter.py + test_adapter.py (15 testes) + integração com verify-mcp, lockfile, DB.
```

| # | Task | Descrição | Arquivo(s) | Validação | Issue |
|---|------|-----------|------------|-----------|-------|
| **1.1** | **adapter.ingest()** | Lê blueprint.yaml → extrai name, tools, sdk, pattern → gera mcp.json + server.py → verify-mcp → lock → register DB | `registry/src/adapter.py` | `adapter.ingest("mcps/example")` → mcp.json válido + verify 0 erros + lockfile + DB | #1 |
| 1.2 | adapter.info() + sync() | info(): retorna manifesto + FSM + runs. sync(): revalida se blueprint mudou | `registry/src/adapter.py` | info() retorna dados corretos. sync() é no-op se nada mudou, erro se verify falha | #2 |
| 1.3 | Testes do adapter | 15 testes parametrizados (4 SDKs × 3 patterns + cenários de erro) | `registry/tests/test_adapter.py` | `pytest -v test_adapter.py` → 15/15 passando | #3 |

**Código esperado da task 1.1:**

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
    7. Retorna {mcp_id, status, manifest_hash}
    """
```

**Código esperado da task 1.3:**

```python
# registry/tests/test_adapter.py

@pytest.mark.parametrize("sdk", ["python", "typescript", "go", "rust"])
@pytest.mark.parametrize("pattern", ["stateless", "event", "factory"])
def test_ingest_sdk_pattern(sdk, pattern, tmp_path):
    """Ingest funciona com qualquer SDK + pattern."""
    ...
    assert result["ok"]
```

---

### ETAPA 2 — Templates Complementares

```
🎯 Objetivo: mcp-builder gera mcp.json + server.py junto com o projeto.
📦 Entrega: 12 arquivos mcp.json.hbs + 1 server.py.hbs.
```

| # | Task | Descrição | Arquivo(s) | Validação | Issue |
|---|------|-----------|------------|-----------|-------|
| **2.1** | **mcp.json.hbs** | Template Handlebars que gera mcp.json compatível com schema do mcps-as-objects | `templates/*/mcp.json.hbs` (12 arquivos) | `npx mcp-builder new x --sdk python --pattern stateless` → gera mcp.json válido | #4 |
| **2.2** | **server.py.hbs** | Template Handlebars que gera FastMCP wrapper (importa de core, expõe tools como @mcp.tool()) | `templates/python-sdk/*/src/server.py.hbs` | `python src/server.py` inicia sem erro. verify-mcp passa | #5 |

**MCP.json gerado (exemplo):**

```jsonc
{
  "id": "sentiment-analyzer",      // ← do blueprint.name (convertido para kebab)
  "name": "Sentiment Analyzer",     // ← do blueprint.name
  "version": "0.1.0",
  "description": "...",             // ← do blueprint.description
  "entry": "src/server.py",
  "runtime": {
    "language": "python",           // ← do blueprint.sdk
    "image": "ubuntu-22.04"
  },
  "functions": [
    {
      "name": "analyze",           // ← de blueprint.tools[].name (convertido para snake)
      "description": "...",
      "input_schema": {},           // ← de blueprint.tools[].inputSchema
      "output_schema": {}
    }
  ],
  "platforms": ["*"],
  "blueprint": {
    "sdk": "python",                // ← metadata original
    "pattern": "factory",           // ← metadata original
    "hooks": ["cost-limit"]         // ← metadata original
  }
}
```

---

### ETAPA 3 — Automação do Fluxo

```
🎯 Objetivo: mcp-builder → adapter.ingest() automático via hook.
📦 Entrega: Hook pós-scaffold + CI/CD integrado.
```

| # | Task | Descrição | Arquivo(s) | Validação | Issue |
|---|------|-----------|------------|-----------|-------|
| **3.1** | **Hook pós-scaffold** | Hook que dispara adapter.ingest() automaticamente após mcp-builder gerar um projeto | `mcp-builder/hooks/post-scaffold.ts` | `mcp-builder new x` → hook chama adapter → MCP registrado automaticamente | #6 |
| 3.2 | CI/CD builder→registry | Workflow que após scaffold bem-sucedido, chama adapter.ingest() e reporta resultado | `.github/workflows/builder-register.yml` | PR com novo MCP → CI valida + registra automaticamente | #6 |

---

### ETAPA 4 — Unificação FSM + Blueprint

```
🎯 Objetivo: Registry expõe FSM e Blueprint dos MCPs gerados pelo mcp-builder.
📦 Entrega: Endpoints de FSM + Blueprint + visibilidade no mcpsctl.
```

| # | Task | Descrição | Arquivo(s) | Validação | Issue |
|---|------|-----------|------------|-----------|-------|
| **4.1** | **FSM no Registry** | Ler .mcp/state/states.yaml + transitions.yaml e expor via API | `registry/src/fsm_reader.py` + `api.py` | `GET /mcps/{id}/fsm` → estados + transições. `GET /mcps/{id}/fsm/mermaid` → diagrama | #7 |
| **4.2** | **Blueprint no Registry** | Ler blueprint.yaml e expor via API + CLI | `registry/src/api.py` + `cli.py` | `GET /mcps/{id}/blueprint` → blueprint parseado. `mcpsctl describe` mostra blueprint | #8 |

---

### ETAPA 5 — Governança Cross-Platform

```
🎯 Objetivo: 5 hooks de governança do mcp-builder disponíveis no Registry.
📦 Entrega: Hooks portados (Python + TS), endpoints de execução, documentação.
```

| # | Task | Descrição | Arquivo(s) | Validação | Issue |
|---|------|-----------|------------|-----------|-------|
| **5.1** | **5 hooks de governança** | cost-limit (gate), rate-limit (gate), audit-log (monitor), dependency-vulns (advisor), prompt-injection-detector (gate) | `registry/src/hooks/*.py` | Cada hook: versão Python + versão TS. `POST /mcps/{id}/hooks/run?hook=rate-limit` → executa. 5+ testes por hook | #9 |
| 5.2 | Documentação final | GOVERNANCE.md atualizado + README.md atualizado + docs/hooks.md | `docs/` | Documento cobre todos os hooks com exemplos de uso | — |

---

## ═══════════════════════════════════════════════════════════════════
## 4. DEPENDÊNCIAS ENTRE ETAPAS
## ═══════════════════════════════════════════════════════════════════

```
ETAPA 0: Fundação
  ├── Nenhuma dependência (pode começar imediatamente)
  │
  ├──▶ ETAPA 1: Bridge Core
  │     ├── Depende: Etapa 0 (GitHub Project + Issues)
  │     └── Libera: mcp-builder pode gerar MCPs que são ingeridos
  │
  ├──▶ ETAPA 2: Templates Complementares
  │     ├── Depende: Etapa 0 (GitHub Project + Issues)
  │     └── Libera: mcp-builder gera mcp.json + server.py nativamente
  │
  ├──▶ ETAPA 3: Automação do Fluxo
  │     ├── Depende: Etapa 1 (adapter.ingest()) + Etapa 2 (templates)
  │     └── Libera: fluxo automático mcp-builder → registry
  │
  ├──▶ ETAPA 4: Unificação FSM + Blueprint
  │     ├── Depende: Etapa 1 (adapter.info())
  │     └── Libera: visibilidade completa do FSM + Blueprint
  │
  └──▶ ETAPA 5: Governança Cross-Platform
        ├── Depende: Etapa 0 a 4
        └── Libera: ecossistema completo com governança
```

---

## ═══════════════════════════════════════════════════════════════════
## 5. GITHUB PROJECT — KANBAN
## ═══════════════════════════════════════════════════════════════════

### Board

```
MCP-MANAGER INTEGRATION
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ 📋       │  │ 🏗️      │  │ ✅       │  │ 🚀       │  │ 📦       │
│ Backlog  │→│ Doing    │→│ Review   │→│ Staging  │→│ Done     │
│          │  │          │  │          │  │          │  │          │
│ Issues   │  │ Em       │  │ PR       │  │ Testado  │  │ Fechado  │
│ sem      │  │ execução │  │ aberto   │  │ em CI    │  │          │
│ início   │  │          │  │          │  │          │  │          │
└──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘
```

### Labels

```
fase-0-fundacao       🔵 #0052cc
fase-1-bridge         🔵 #0052cc
fase-2-templates      🟢 #008672
fase-3-automacao      🟠 #d93f0b
fase-4-unificacao     🟣 #5319e7
fase-5-governanca     🔴 #b60205
compliance            🟡 #ffe82a
test                  🟢 #28a745
docs                  🔵 #6f42c1
bug                   🔴 #d73a4a
```

### Milestones

```
M0 — Fundação       (Etapa 0)
M1 — Bridge Core    (Etapa 1)
M2 — Templates      (Etapa 2)
M3 — Automação      (Etapa 3)
M4 — Unificação     (Etapa 4)
M5 — Governança     (Etapa 5)
```

---

## ═══════════════════════════════════════════════════════════════════
## 6. FLUXO DE EXECUÇÃO (event-driven no GitHub)
## ═══════════════════════════════════════════════════════════════════

### 6.1 Para o desenvolvedor

```
1. Pegar issue do Backlog
2. Mover para Doing (automático via label)
3. Implementar (código + testes)
4. Abrir PR → move para Review (automático)
5. CI roda verify-mcp + pytest
6. Aprovar PR → merge → move para Done (automático)
```

### 6.2 Automação (workflows)

```
Evento: Issue aberta
Ação:  Cria card no Backlog
Workflow: project-automation.yml

Evento: Label de fase aplicada
Ação:  Move card para Doing
Workflow: project-automation.yml

Evento: PR aberto
Ação:  Move card para Review
Workflow: project-automation.yml

Evento: Card move para Review
Ação:  Roda verify-mcp --all + pytest adapter
Workflow: card-validate.yml

Evento: PR merged
Ação:  Move card para Done
Workflow: project-automation.yml
```

---

## ═══════════════════════════════════════════════════════════════════
## 7. RESUMO — 6 ETAPAS, 10 TASKS, 5 MILESTONES
## ═══════════════════════════════════════════════════════════════════

```
┌────────┬──────────────────────────────┬───────┬──────────────────────────┐
│ Etapa  │ Nome                         │ Tasks │ Milestone                │
├────────┼──────────────────────────────┼───────┼──────────────────────────┤
│ 0      │ Fundação                     │ 4     │ M0 — Fundação            │
│ 1      │ Bridge Core                  │ 3     │ M1 — Bridge Core         │
│ 2      │ Templates Complementares     │ 2     │ M2 — Templates           │
│ 3      │ Automação do Fluxo           │ 2     │ M3 — Automação           │
│ 4      │ Unificação FSM + Blueprint   │ 2     │ M4 — Unificação          │
│ 5      │ Governança Cross-Platform    │ 2     │ M5 — Governança          │
├────────┴──────────────────────────────┼───────┼──────────────────────────┤
│ TOTAL                                 │ 15    │ 6 milestones             │
└─────────────────────────────────────────────────────────────────────────┘
```

### O que é ENTREGUE ao final

```
□ mcp-builder integrado como submódulo/diretório
□ adapter.py (bridge) funcional: ingest, info, sync
□ 15 testes do adapter passando
□ 12 templates mcp.json.hbs gerando manifesto compatível
□ 1 template server.py.hbs gerando FastMCP wrapper
□ Hook pós-scaffold automatizando ingest
□ FSM exposto no Registry
□ Blueprint exposto no Registry
□ 5 hooks de governança portados
□ Workflows de automação do Kanban
□ GitHub Project com 10 cards organizados
□ 6 milestones concluídas
□ Tudo versionado na branch feat/pi-ecosystem-management
□ Escopo total: ~95% coberto
```

---

**Status: Plano concluído e aprovado. Aguardando ordem para iniciar a Etapa 0 (Fundação).** 🚀
