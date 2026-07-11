# 🏗️ mcps-as-objects — Projeto & Arquitetura

> **Documento vivo** para incremento, análise e compreensão contínua do sistema.

---

## 1. Conceito

**mcps-as-objects** é um sistema determinístico para criar, catalogar, validar, executar e compor **MCPs (Model Context Protocol servers)** como objetos gerenciados.

Cada MCP é um **objeto** com:
- 📦 **Manifesto** (`mcp.json`) — contrato que define o que o MCP faz
- 🧬 **Implementação** (`src/server.py`) — o servidor MCP de fato
- 🧪 **Testes** (`tests/`) — verificação de funcionamento
- 🔑 **Lockfile** (SHA-256) — identificador único para cache e rastreabilidade
- 🎯 **Plataforma** — declara onde funciona (android/termux, linux/amd64, etc.)

---

## 2. Arquitetura em Camadas

```
┌──────────────────────────────────────────────────────────────────┐
│                         CONSUMIDORES                              │
│    pi-coding-agent    CLI (mcpsctl)    curl/HTTP    GitHub Actions │
└────────────────────────────┬─────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│                     REGISTRY BACKEND (Python)                      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐  │
│  │  MCP Server     │  │  HTTP API      │  │  CLI (mcpsctl)    │  │
│  │  (FastMCP/stdio)│  │  (FastAPI)     │  │  (Typer)          │  │
│  │  para pi        │  │  para workflows│  │  para dev         │  │
│  └────────┬───────┘  └───────┬────────┘  └─────────┬──────────┘  │
│           │                  │                      │             │
│  ┌────────▼──────────────────▼──────────────────────▼──────────┐ │
│  │                   Core Modules                              │ │
│  │  ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌───────┐ ┌──────┐   │ │
│  │  │ db.py   │ │ crud.py  │ │ catalog │ │valid. │ │snap. │   │ │
│  │  │(SQLite) │ │ (CRUD)   │ │ .py     │ │.py    │ │hot.py│   │ │
│  │  └─────────┘ └──────────┘ └─────────┘ └───────┘ └──────┘   │ │
│  │  ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌───────┐ ┌──────┐   │ │
│  │  │constr.  │ │composer  │ │platdet. │ │verif. │ │snap. │   │ │
│  │  │.py      │ │.py       │ │py       │ │er.py  │ │hot.py│   │ │
│  │  └─────────┘ └──────────┘ └─────────┘ └───────┘ └──────┘   │ │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│                    DATA LAYER                                      │
│  ┌──────────────────────┐  ┌──────────────────┐  ┌────────────┐  │
│  │  SQLite              │  │  mcps-lock.json   │  │  Schemas/  │  │
│  │  (mcps, functions,   │  │  (SHA-256 hashes) │  │  (JSON     │  │
│  │   runs, migrations)  │  │                   │  │   Schema)  │  │
│  └──────────────────────┘  └──────────────────┘  └────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│                    MCPS CATALOG (mcps/<id>/)                       │
│                                                                   │
│  mcps/                                                            │
│  ├── _template/              → Template determinístico            │
│  ├── example-greeter/        → Exemplo funcional (universal)      │
│  ├── processador-texto/      → Exemplo replicável (universal)     │
│  ├── python-termux-builder/  → Só android/termux                  │
│  └── meu-novo-servico/       → Criado pelo constructor            │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Fluxo de Criação de um MCP (Pre-Staging)

```
[Dev] mcpsctl new meu-servico
  │
  ▼
┌────────────────────────────────────────────────────────────┐
│ 1. CONSTRUCTOR                                             │
│   • Copia _template/ → mcps/meu-servico/                  │
│   • Preenche placeholders (id, name, desc, version)       │
│   • Gera mcp.json, src/server.py, tests/, README.md       │
│                                                            │
│ Garantias: ID kebab-case ✓, estrutura padrão ✓             │
└────────────────────────────────────────────────────────────┘
  │
  ▼
┌────────────────────────────────────────────────────────────┐
│ 2. SCHEMA VALIDATION                                       │
│   • Valida mcp.json contra mcp-manifest.schema.json        │
│   • Valida function-io.schema.json para input/output       │
│                                                            │
│ Garantias: Contrato válido ✓                               │
└────────────────────────────────────────────────────────────┘
  │
  ▼
┌────────────────────────────────────────────────────────────┐
│ 3. VERIFY-MCP (15 checks)                                  │
│   📁 Estrutura de diretórios                               │
│   📜 Manifesto (schema, id, funções, platforms)           │
│   🔧 server.py @mcp.tool() condizentes                    │
│   🧪 Testes existem e compilam                            │
│   📦 Lockfile com SHA-256                                  │
│   💾 Cache key = f(lockfile) — isolado                    │
│   🚀 Pode ser disparado individualmente                   │
│   📱 Plataforma válida                                     │
│                                                            │
│ Garantias: 0 erros ✓                                        │
└────────────────────────────────────────────────────────────┘
  │
  ▼
┌────────────────────────────────────────────────────────────┐
│ 4. LOCKFILE (SHA-256)                                      │
│   • mcpsctl lock → atualiza mcps-lock.json                 │
│   • Hash = sha256(mcp.json)                                │
│   • Cache key = sha256(mcps-lock.json) + sha256(uname)    │
│                                                            │
│ Garantias: Lockfile + hash consistentes ✓                   │
└────────────────────────────────────────────────────────────┘
  │
  ▼
┌────────────────────────────────────────────────────────────┐
│ 5. DATABASE                                                │
│   • register_mcp() → SQLite (mcps.functions, runs)        │
│   • Registry API disponível                                │
│                                                            │
│ Garantias: Persistido ✓                                     │
└────────────────────────────────────────────────────────────┘
  │
  ▼
┌────────────────────────────────────────────────────────────┐
│ 6. EVENT-DRIVEN DISPATCH                                   │
│   gh workflow run mcp-runtime.yml -f mcp_id=meu-servico   │
│   → Executa APENAS este MCP                                │
│   → Cache hit se lockfile não mudou                        │
│                                                            │
│ Garantias: Isolado ✓, cache isolado ✓                      │
└────────────────────────────────────────────────────────────┘
```

---

## 4. Componentes do Registry

### 4.1 Core Modules

| Módulo | Função | Dependências |
|--------|--------|--------------|
| `db.py` | SQLite connection, migrations, schema | sqlite3 (stdlib) |
| `crud.py` | Create/Read/Update/Delete de MCPs + functions + runs | db, catalog |
| `catalog.py` | Leitura de manifestos do filesystem, lockfile | stdlib |
| `validator.py` | Validação de manifestos contra JSON Schema | fastjsonschema |
| `constructor.py` | Cria novos MCPs a partir do template | shutil, json |
| `composer.py` | Pipeline/DAG entre MCPs | dataclasses |
| `snapshot.py` | Cache key SHA-256 determinística | hashlib, subprocess |
| `platdetect.py` | Detecção de plataforma + filtro | stdlib |
| `verifier.py` | Pós-criação: executa verify-mcp.py | subprocess |

### 4.2 Interfaces

| Interface | Transporte | Porta / Protocolo | Uso principal |
|-----------|-----------|-------------------|---------------|
| **API HTTP** | TCP | :8712 (FastAPI) | Workflows, curl, testes |
| **MCP Server** | stdio | stdin/stdout (FastMCP) | pi-coding-agent |
| **CLI** | terminal | `tools/mcpsctl` | Desenvolvimento local |

### 4.3 Endpoints da API

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/health` | Status do registry |
| GET | `/mcps` | Lista todos MCPs |
| GET | `/mcps/{id}` | Detalhe de um MCP |
| GET | `/mcps/{id}/manifest` | Manifesto completo |
| GET | `/mcps/{id}/functions` | Funções de um MCP |
| DELETE | `/mcps/{id}` | Remove MCP do DB |
| POST | `/mcps/{id}/run` | Executa função inline |
| POST | `/mcps/{id}/validate` | Valida manifesto |
| POST | `/mcps/{id}/dispatch` | 🚀 Dispara workflow event-driven |
| GET | `/mcps/{id}/compatibility` | Compatibilidade com plataforma |
| GET | `/mcps/compatible` | Lista MCPs compatíveis |
| POST | `/registry/scan` | Reescaneia filesystem |
| GET | `/snapshot/key` | Chave de cache SHA-256 |
| GET | `/platform` | Info da plataforma atual |
| GET | `/pipeline/graph` | DAG de dependências |

### 4.4 Tools do MCP Server (stdio)

| Tool | Descrição |
|------|-----------|
| `list_mcps()` | Lista MCPs catalogados |
| `describe_mcp(id)` | Manifesto completo |
| `create_mcp(id, name, desc)` | Cria novo MCP |
| `run_mcp_function(id, fn, args)` | Executa função |
| `validate_mcp(id)` | Valida manifesto |
| `cache_key()` | Chave de cache SHA-256 |
| `pipeline_info()` | Info de pipeline/DAG |
| `platform_info()` | Plataforma + MCPs compatíveis |

---

## 5. Estrutura de Diretórios (Padrão Obrigatório)

```
mcps-as-objects/
├── .github/workflows/         # Workflows GitHub Actions
│   ├── mcp-runtime.yml        # 🏭 Pipeline principal (batch ou single)
│   ├── mcp-single.yml         # 🚀 Event-driven (1 MCP por execução)
│   ├── mcp-cache.yml          # 💾 Build de snapshot
│   ├── mcp-validate.yml       # ✅ CI validação de schema
│   └── mcp-verify.yml         # 🔍 CI verificação completa (15 checks)
│
├── schemas/                   # 📐 Fonte da verdade
│   ├── mcp-manifest.schema.json
│   ├── function-io.schema.json
│   └── lockfile.schema.json
│
├── mcps/                      # 📦 MCPs catalogados
│   ├── _template/             #     Template determinístico
│   │   ├── mcp.json           #     📜 Manifesto
│   │   ├── src/server.py      #     🔧 Servidor FastMCP
│   │   ├── tests/test_*.py    #     🧪 Testes
│   │   └── README.md          #     📖 Documentação
│   └── <mcp-id>/              #     (mesma estrutura)
│
├── registry/                  # ⚙️ Registry Backend
│   ├── src/
│   │   ├── db.py              #     SQLite + migrations
│   │   ├── crud.py            #     CRUD operations
│   │   ├── catalog.py         #     Leitura de manifestos
│   │   ├── validator.py       #     Validação JSON Schema
│   │   ├── constructor.py     #     Criador de MCPs
│   │   ├── composer.py        #     Pipeline/composição
│   │   ├── snapshot.py        #     Cache key SHA-256
│   │   ├── platdetect.py      #     Detector de plataforma
│   │   ├── verifier.py        #     Pós-criação verify
│   │   ├── api.py             #     HTTP API (FastAPI)
│   │   ├── server.py          #     MCP stdio (FastMCP)
│   │   └── cli.py             #     CLI (Typer)
│   ├── data/                  #     SQLite DB (runtime)
│   └── tests/
│
├── scripts/                   # 🔧 Scripts auxiliares
│   ├── compute-key.py         #     Cache key SHA-256
│   ├── build-db.py            #     Build SQLite
│   ├── list-mcps.py           #     Lista MCPs (com filtro)
│   ├── execute-mcp.py         #     Executa 1 MCP
│   ├── consolidate.py         #     Consolida resultados
│   └── verify-mcp.py          #     15 checks de conformidade
│
├── tools/                     # 🔧 Ferramentas de dev
│   ├── mcpsctl                #     CLI principal
│   ├── bootstrap.sh           #     Setup inicial
│   └── snapshot.sh            #     Cache helpers
│
├── docs/                      # 📖 Documentação
│   ├── ARCHITECTURE.md        #     Arquitetura do sistema
│   ├── GOVERNANCE.md          #     📜 Regras e governança
│   ├── PATTERNS.md            #     Convenções determinísticas
│   ├── MCP-AUTHORING.md       #     Guia de criação de MCPs
│   └── WORKFLOW-RUNTIME.md    #     Execução em GitHub Actions
│
├── mcps-lock.json             # 📌 Lockfile (SHA-256)
├── requirements.txt
├── Makefile
└── README.md
```

---

## 6. Modelo de Dados (SQLite)

```sql
-- Tabela principal de MCPs
mcps (
    id TEXT PRIMARY KEY,          -- kebab-case
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    description TEXT,
    manifest_path TEXT NOT NULL,
    manifest_hash TEXT NOT NULL,  -- SHA-256 do mcp.json
    registered_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Funções expostas por cada MCP
functions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mcp_id TEXT NOT NULL,          -- FK → mcps.id
    name TEXT NOT NULL,           -- snake_case
    description TEXT,
    input_schema TEXT,            -- JSON Schema
    output_schema TEXT,           -- JSON Schema
    UNIQUE (mcp_id, name)
);

-- Histórico de execuções
runs (
    id TEXT PRIMARY KEY,          -- UUID
    mcp_id TEXT NOT NULL,
    function_name TEXT NOT NULL,
    input_payload TEXT,
    output_payload TEXT,
    status TEXT CHECK (status IN ('pending','ok','error')),
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    workflow_run_id TEXT
);
```

---

## 7. Cache e Performance

### 7.1 Estratégia

```
cache_key = "mcp-snapshot-v1-{sha256(mcps-lock.json)}-{sha256(uname)[:12]}"
```

| Situação | Cache | Tempo |
|----------|-------|-------|
| Lockfile não mudou | HIT → restaura .venv + DB | ~3s |
| Lockfile mudou | MISS → instala deps + build DB | ~3min |
| Primeira execução | MISS → tudo do zero | ~3min |
| Novo MCP adicionado | MISS (lockfile mudou) | ~3min |

### 7.2 O que é cacheado

- `.venv/` — virtualenv com todas as dependências
- `registry/data/registry.db` — SQLite com MCPs registrados
- `.cache/snapshot/` — snapshot completo para workers

### 7.3 Cache é isolado por SHA-256

```python
# Se mcps-lock.json muda → hash muda → cache key muda
# Snapshot anterior NUNCA contamina o novo estado
lock_hash = hashlib.sha256(lock_data).hexdigest()
```

---

## 8. Plataformas

### 8.1 Detecção Automática

O módulo `platdetect.py` detecta:

```python
detect_platform()  # → "android/termux" | "linux/amd64" | "linux/arm64" | ...
detect_platforms() # → ["android/termux", "linux/aarch64", "*"]
```

### 8.2 Filtro de MCPs

```python
# MCPs que funcionam NESTA máquina
GET /mcps/compatible

# Exemplo: em linux/amd64, python-termux-builder é ocultado
# Em android/termux, python-termux-builder aparece
```

---

## 9. Event-Driven

### 9.1 Chamada Individual

```bash
# Executa SOMENTE python-termux-builder
gh workflow run mcp-runtime.yml \
  -f mcp_id=python-termux-builder \
  --repo camillanapoles/mcps-as-objects
```

### 9.2 Chamada via API

```bash
# Dispara workflow para 1 MCP via HTTP
curl -X POST http://localhost:8712/mcps/python-termux-builder/dispatch
# → 202 Accepted: { "run_id": "...", "status": "dispatched" }
```

### 9.3 Isolamento

- Cada `mcp_id` gera seu próprio job no GitHub Actions
- Falha em MCP-A não afeta MCP-B
- Cache é compartilhado (mesmo lockfile) mas execução é isolada

---

## 10. Segurança e Integridade

| Mecanismo | O que protege |
|-----------|---------------|
| SHA-256 do manifesto | Integridade do mcp.json |
| SHA-256 do lockfile | Integridade de todo o catálogo |
| Schema validation | Contrato contra manifestos malformados |
| 15 checks verify | Conformidade estrutural e funcional |
| Platform filter | Execução apenas em máquinas compatíveis |
| Cache isolation | Snapshot não contamina entre versões |

---

## 11. Métricas e Monitoramento

### 11.1 O que observar

- **Cache hit ratio** → quantas execuções reusam snapshot vs. constroem do zero
- **Tempo de execução** → worker job duration por MCP
- **Taxa de aprovação do verify** → quantos PRs passam nos 15 checks
- **MCPs por plataforma** → distribuição de compatibilidade

### 11.2 Onde ver

- GitHub Actions → `mcp-runtime.yml` → job durations
- GitHub Actions → `mcp-verify.yml` → pass/fail ratio
- SQLite → `runs` table → histórico de execuções

---

## 12. Evolução do Projeto

### 12.1 Próximas Features Possíveis

- [ ] **Pipeline chaining**: output de MCP A → input de MCP B automaticamente
- [ ] **MCP versioning**: múltiplas versões do mesmo MCP (semver no path)
- [ ] **Dependency resolver**: detectar dependências transitivas de pacotes Python
- [ ] **Webhook trigger**: evento externo dispara MCP via webhook
- [ ] **Dashboard UI**: interface web para gerenciar MCPs
- [ ] **Multi-repo**: MCPs em repositórios separados com referência no lockfile
- [ ] **MCP marketplace**: publish/compartilhar MCPs entre projetos

### 12.2 Como Contribuir

1. Leia `docs/GOVERNANCE.md`
2. Siga `docs/PATTERNS.md` para nomenclatura
3. Use `mcpsctl new <id>` para criar novo MCP
4. Rode `python3 scripts/verify-mcp.py <id>` antes de commitar
5. Garanta que o CI (`mcp-verify.yml`) passe
