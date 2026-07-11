# ⚡ Critérios de Uso — Local vs GitHub Actions (Workflow)

> Guia de decisão: quando um MCP roda **local** (stdio/HTTP, ms) e quando roda **remoto** (GitHub Actions, minutos).

---

## 1. As Duas Faces de Cada MCP

Todo MCP neste ecossistema pode operar em **dois modos**:

```
┌──────────────────────────────────────────────────────────────────┐
│                        MCP OBJECT                                 │
│                                                                   │
│  ┌─────────────────────┐        ┌────────────────────────────┐   │
│  │  FACE LOCAL         │        │  FACE REMOTA               │   │
│  │                     │        │                             │   │
│  │  Transporte: stdio  │        │  Transporte: GitHub Actions │   │
│  │  Latência: ms       │        │  Latência: 30s ~ 5min      │   │
│  │  Estado: SQLite     │        │  Estado: efêmero (job)     │   │
│  │  Consumidor: pi     │        │  Consumidor: gh CLI / API  │   │
│  └─────────────────────┘        └────────────────────────────┘   │
│                                                                   │
│  Ex: python-termux-builder                                        │
│    Local:  check_package()  → 50ms   (consulta catálogo)         │
│    Remoto: build_wheel()    → 3min   (cross-compila Rust)        │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. Matriz de Decisão

| Requisito | Local (stdio/HTTP) | Remoto (GitHub Actions) | Decisão |
|-----------|-------------------|------------------------|---------|
| **Latência** | ✅ 1~100ms | ❌ 30s~5min | **Local** se precisa de resposta rápida |
| **Computação pesada** | ❌ CPU/GPU limitada | ✅ 4 vCPU, 16GB RAM | **Remoto** se compila, processa dados |
| **Toolchain nativa** | ❌ Termux sem Rust | ✅ Ubuntu completo | **Remoto** se precisa de gcc, rustc, etc. |
| **Estado persistente** | ✅ SQLite | ❌ Job morre no fim | **Local** se acumula estado |
| **Interação pi-agent** | ✅ stdio vivo | ❌ Workflow headless | **Local** para chat com pi |
| **CI/CD / Schedule** | ❌ Sem cron nativo | ✅ CRON + PR hooks | **Remoto** para automação |
| **Conexão externa** | ✅ HTTP client | ✅ HTTP client | **Ambos** — depende do resto |
| **Custo financeiro** | ✅ Grátis (seu hardware) | ⚠️ 2000 min/mês free | **Local** se quer evitar custo |
| **Paralelismo** | ✅ Assíncrono | ✅ Matrix jobs | **Ambos** |
| **Segredo/env vars** | ✅ Local | ✅ GitHub Secrets | **Ambos** |

---

## 3. Árvore de Decisão

```
O que o MCP precisa fazer?
│
├─ Consultar dados, validar, catalogar?
│  → LOCAL (stdio/HTTP)
│  │  └─ Ex: check_package(), check_requirements(), validate_mcp()
│  │  └─ Tempo: milissegundos
│  │  └─ Consumidor: pi-coding-agent, curl, CLI
│  │
├─ Compilar, buildar, processar pesado?
│  → REMOTO (GitHub Actions)
│  │  └─ Ex: build_wheel('rpds-py'), pipeline de dados
│  │  └─ Tempo: minutos
│  │  └─ Consumidor: gh CLI, POST /dispatch
│  │
├─ Interagir com usuário em tempo real?
│  → LOCAL (stdio)
│  │  └─ Ex: pi perguntar "qual MCP disponível?"
│  │  └─ Conversa síncrona, sem delay
│  │
├─ Rodar em schedule / toda semana?
│  → REMOTO (CRON workflow)
│  │  └─ Ex: mcp-cache.yml, rebuild semanal
│  │
├─ Precisa de dependência nativa (Rust, C)?
│  → REMOTO (GitHub Actions)
│  │  └─ Ex: pydantic-core, rpds-py, cryptography
│  │  └─ Ubuntu tem gcc, rustc, cmake, etc.
│  │
├─ Precisa responder o pi-agent via MCP protocol?
│  → LOCAL (stdio)
│  │  └─ pi precisa de um processo VIVO respondendo
│  │  └─ Workflow não mantém processo vivo
│  │
└─ Ambos?
    → SEPARAR lógica leve (core.py) da pesada (workflow)
       core.py → LOCAL (testável, rápido)
       workflow → REMOTO (orquestrado via POST /dispatch)
```

---

## 4. Padrão de Implementação

### Estrutura recomendada para um MCP com as duas faces

```
mcps/meu-mcp/
├── mcp.json              # Manifesto (functions descrevem ambos)
├── src/
│   ├── core.py           # 🔧 Lógica PURA (sem MCP SDK)
│   │                     #   → Testável sem dependências externas
│   │                     #   → Usada tanto local quanto remoto
│   └── server.py         # 🔧 FastMCP wrapper (LOCAL)
│                          #   → Importa de core.py
│                          #   → Tools respondem em ms
├── tests/
│   └── test_smoke.py     # 🧪 Testa core.py (não server.py)
└── .github/workflows/
    └── meu-mcp.yml       # 🚀 REMOTO (se aplicável)
```

### Regras

1. **`core.py`** contém toda a lógica de negócio — **zero dependência do MCP SDK**
2. **`server.py`** é um wrapper fino que importa `core.py` e registra `@mcp.tool()`
3. **Testes** testam `core.py` diretamente — podem rodar em qualquer ambiente (inclusive Termux sem `mcp` instalado)
4. **Workflow** (se houver face remota) chama `scripts/execute-mcp.py` que importa `server.py`
5. O manifesto `mcp.json` descreve as funções — **não importa se a implementação é local ou remota**

---

## 5. Exemplo Concreto: `python-termux-builder`

```python
# ── mcps/python-termux-builder/src/core.py ──
# Lógica PURA, testável, sem MCP SDK
def check_package(pkg): ...
def build_wheel(pkg): ...
def list_cached_wheels(): ...
def check_requirements(text): ...
```

```python
# ── mcps/python-termux-builder/src/server.py ──
# Apenas registra tools no FastMCP (FACE LOCAL)
from core import check_package, build_wheel, ...

@mcp.tool()
def check_package_tool(pkg): return check_package(pkg)  # LOCAL: 50ms
@mcp.tool()
def build_wheel_tool(pkg): return build_wheel(pkg)      # LOCAL: mostra instruções
```

```
# ── .github/workflows/mcp-single.yml ──
# FACE REMOTA: executa em runner Ubuntu
# Guarda: 30s boot + execução
# Consumidor: gh workflow run ou POST /dispatch
```

### O que cada face faz:

| Face | check_package | build_wheel | list_cached_wheels | check_requirements |
|------|---------------|-------------|---------------------|--------------------|
| **LOCAL** (stdio/HTTP) | ✅ 50ms | ✅ instruções (gh não disponível) | ✅ 10ms | ✅ 80ms |
| **REMOTO** (workflow) | ❌ não faz sentido (leve) | ✅ 3min (cross-compila Rust) | ❌ não faz sentido | ❌ não faz sentido |

---

## 6. Quando Usar Cada Workflow

### Local (síncrono, ms)

```bash
# Via MCP stdio (pi-agent)
tools/mcpsctl serve-mcp
# → pi se conecta e chama tools em tempo real

# Via HTTP API
make run-api
curl http://localhost:8712/mcps/python-termux-builder/compatibility

# Via CLI inline
python3 -c "from core import check_package; print(check_package('rpds-py'))"
```

### Remoto (assíncrono, minutos)

```bash
# Disparar MCP individual (event-driven)
gh workflow run mcp-runtime.yml \
  -f mcp_id=python-termux-builder \
  --repo camillanapoles/mcps-as-objects

# Ou via API (dispara workflow automaticamente)
curl -X POST http://localhost:8712/mcps/python-termux-builder/dispatch
# → 202 Accepted, run_id retornado

# Acompanhar
gh run view <run-id> --repo camillanapoles/mcps-as-objects --watch
```

---

## 7. Resumo Visual

```
                    TEMPO REAL?                  COMPUTAÇÃO PESADA?
                    ├── Sim → LOCAL (stdio)       ├── Sim → REMOTO (workflow)
                    │    pi-agent, ms             │    Compilar, build, 3min
                    │                             │
                    └── Não → veja ao lado        └── Não → LOCAL (API)
                                                       CRUD, consulta, ms

                    PRECISA DE TOOLCHAIN?         INTERAGE COM PI?
                    ├── Sim → REMOTO              ├── Sim → LOCAL (stdio)
                    │    Rust, C, gcc             │    Chat, perguntas
                    │                             │
                    └── Não → LOCAL (API)         └── Não → gh CLI ou API
```

---

## 8. Boas Práticas

1. **Sempre comece com `core.py`** — lógica pura, testável sem MCP SDK
2. **Adicione `server.py`** só quando precisar expor via protocolo MCP (pi-agent)
3. **Adicione workflow** só quando a operação precisar de computação que a máquina local não tem
4. **Mantenha o manifesto (`mcp.json`) descrevendo a função** — não importa se local, remoto ou ambos
5. **Testes sempre em `core.py`** — rodam em qualquer ambiente
6. **Se a operação é leve (<1s), faça LOCAL** — workflow adiciona 30s+ de overhead
7. **Se a operação precisa de Rust, C, GPU, ou >1min de CPU, faça REMOTO**
