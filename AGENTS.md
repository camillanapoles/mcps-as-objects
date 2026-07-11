# 🧠 Skill do Agente — Guia Completo de Uso e Manutenção

> Instruções permanentes para qualquer agente (IA ou humano) interagir com o projeto **mcps-as-objects**.

---

## ═══════════════════════════════════════════════════════════════
## PARTE 1 — COMO USAR O PROJETO
## ═══════════════════════════════════════════════════════════════

### 1.0 Sem Clone — Tudo via API

O projeto pode ser usado **sem clonar o repositório**. GitHub API permite criar MCPs, disparar workflows e ver resultados remotamente.

| Operação | API | Exemplo |
|----------|-----|---------|
| Criar mcp.json | `PUT /repos/{owner}/{repo}/contents/mcps/{id}/mcp.json` | curl com base64 |
| Criar server.py | `PUT /repos/{owner}/{repo}/contents/mcps/{id}/src/server.py` | curl com base64 |
| Disparar workflow | `POST /repos/{owner}/{repo}/actions/workflows/{id}/dispatches` | curl com inputs |
| Ver resultado | `GET /repos/{owner}/{repo}/actions/runs/{id}` | gh ou curl |
| Baixar artifact | `GET /repos/{owner}/{repo}/actions/artifacts/{id}/zip` | gh ou curl |
| Listar MCPs | `GET /repos/{owner}/{repo}/contents/mcps` | curl |

**Fluxo 100% remoto:**
1. `PUT /contents` → cria `mcp.json` + `src/server.py` no repo
2. `POST /dispatches` → dispara `mcp-runtime.yml` com `mcp_id=<id>`
3. O workflow valida, registra no DB e executa o MCP
4. `GET /actions/runs` + `GET /artifacts` → obtém resultados

> **Clone é necessário apenas para desenvolvimento local** (testes, verify-mcp, API local, server para pi).

### 1.1 Visão Geral

```
mcps-as-objects/
├── mcps/          ← MCPs gerenciados (cada um é um objeto)
├── registry/      ← Backend de gestão (API, DB, CLI)
├── scripts/       ← Scripts de execução
├── schemas/       ← Contratos JSON Schema
├── tools/         ← CLIs
├── docs/          ← Documentação
└── .github/       ← Workflows GitHub Actions
```

### 1.2 Comandos Básicos

```bash
# Listar MCPs disponíveis
python3 scripts/list-mcps.py

# Ver detalhes de um MCP
cat mcps/<id>/mcp.json

# Validar manifesto de um MCP
python3 -c "from validator import validate_manifest_file; print(validate_manifest_file('mcps/<id>/mcp.json'))"

# Verificar MCP completo (15 checks)
python3 scripts/verify-mcp.py <id>

# Verificar TODOS os MCPs
python3 scripts/verify-mcp.py --all

# Atualizar lockfile (após alterar manifesto)
python3 -c "from catalog import *; lock = read_lockfile(); [...] write_lockfile(lock)"

# Rodar testes de um MCP
python3 -m pytest mcps/<id>/tests/

# Rodar testes do registry
python3 -m pytest registry/tests/

# Disparar execução de 1 MCP (event-driven)
gh workflow run mcp-runtime.yml -f mcp_id=<id> --repo camillanapoles/mcps-as-objects
```

### 1.3 Acessar o Registry (API)

```bash
# Iniciar API local
uvicorn registry.src.api:app --host 127.0.0.1 --port 8712 --reload

# Consultar MCPs
curl http://127.0.0.1:8712/mcps

# Ver plataforma atual
curl http://127.0.0.1:8712/platform

# Ver apenas MCPs compatíveis com sua máquina
curl http://127.0.0.1:8712/mcps/compatible
```

---

## ═══════════════════════════════════════════════════════════════
## PARTE 2 — COMO CRIAR UM NOVO MCP (PASSO A PASSO)
## ═══════════════════════════════════════════════════════════════

### 2.1 Fluxo Completo

```
1. CRIAR estrutura → 2. EDITAR manifesto → 3. IMPLEMENTAR core.py
4. CRIAR server.py → 5. ESCREVER testes  → 6. VALIDAR (verify-mcp)
7. ATUALIZAR lockfile → 8. TESTAR dispatch → 9. COMMITAR
```

### 2.2 Passo 1: Criar a Estrutura

```bash
# Opção A: Usando o constructor (recomendado)
python3 -c "
from constructor import create_mcp
create_mcp('meu-servico', name='Meu Serviço', description='Faz algo incrível')
"

# Opção B: Manual (copia do template)
cp -r mcps/_template mcps/meu-servico
# Depois editar mcp.json manualmente
```

**Resultado:**

```
mcps/meu-servico/
├── mcp.json              ← EDITAR (manifesto)
├── src/
│   ├── core.py           ← CRIAR (lógica pura)
│   └── server.py         ← EDITAR (wrapper FastMCP)
├── tests/
│   └── test_smoke.py     ← EDITAR (testes do core.py)
└── README.md             ← EDITAR (documentação)
```

### 2.3 Passo 2: Editar o Manifesto (mcp.json)

```jsonc
{
  "id": "meu-servico",                    // kebab-case, igual ao diretório
  "name": "Meu Serviço",                  // Nome amigável
  "version": "0.1.0",                     // semver
  "description": "Descrição do que faz.",  // Obrigatório
  "entry": "src/server.py",               // Fixo (não mudar)
  "runtime": {
    "language": "python",                 // python | node | go
    "image": "ubuntu-22.04",             // Imagem do runner
    "estimated_duration_sec": 60,        // Tempo estimado
    "dependencies": {
      "python": "requirements.txt"       // Arquivo de deps (opcional)
    }
  },
  "functions": [                          // Lista de funções (mínimo 1)
    {
      "name": "minha_funcao",            // snake_case
      "description": "O que esta função faz.",
      "input_schema": {                   // JSON Schema do input
        "type": "object",
        "properties": {
          "param1": { "type": "string", "description": "..." }
        },
        "required": ["param1"]
      },
      "output_schema": {                  // JSON Schema do output
        "type": "object",
        "properties": {
          "resultado": { "type": "string" }
        },
        "required": ["resultado"]
      }
    }
  ],
  "permissions": [],                      // network:read, exec:shell, etc.
  "pipeline": {                           // Composição (opcional)
    "consumes": [],
    "produces": ["meu-servico.minha_funcao"]
  },
  "platforms": ["*"],                     // Onde funciona: "*" | "android/termux" | "linux/amd64"
  "tags": ["categoria"]
}
```

**Regras do manifesto:**

| Campo | Obrigatório | Regra |
|-------|-------------|-------|
| `id` | ✅ | kebab-case, igual ao diretório |
| `name` | ✅ | Livre |
| `version` | ✅ | semver |
| `description` | ✅ | Texto |
| `entry` | ✅ | Sempre `src/server.py` |
| `runtime.language` | ✅ | python, node, go |
| `runtime.image` | ✅ | `ubuntu-22.04` |
| `functions[]` | ✅ | Mínimo 1 |
| `functions[].name` | ✅ | snake_case |
| `functions[].input_schema` | ✅ | type=object + properties |
| `functions[].output_schema` | ✅ | type + properties |
| `platforms` | ⚠️ | Recomendado definir explicitamente |
| `permissions` | ❌ | Opcional |
| `pipeline` | ❌ | Opcional |
| `tags` | ❌ | Opcional |

### 2.4 Passo 3: Implementar core.py (Lógica Pura)

```python
# mcps/meu-servico/src/core.py
# REGRA: SÓ usar stdlib. NUNCA importar mcp, fastapi, etc.
# REGRA: Testável sem dependências externas.
# REGRA: Cada função pública deve ter type hints e docstring.

from typing import Optional
from datetime import datetime, timezone


def minha_funcao(param1: str, opcional: Optional[str] = None) -> dict:
    """
    O que esta função faz.

    Args:
        param1: Descrição do parâmetro.
        opcional: Parâmetro opcional.

    Returns:
        dict: Resultado com campos esperados.
    """
    # Sua lógica aqui
    return {
        "resultado": f"Processado: {param1}",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
```

### 2.5 Passo 4: Criar server.py (Wrapper FastMCP)

```python
# mcps/meu-servico/src/server.py
# REGRA: Apenas wrapper. Lógica fica em core.py.
# REGRA: FastMCP(name="...") — SÓ name (sem description, sem version)

from mcp.server.fastmcp import FastMCP
from core import minha_funcao as _minha_funcao

mcp = FastMCP(name="meu-servico")

@mcp.tool()
def minha_funcao(param1: str, opcional: str = None) -> dict:
    """
    O que esta função faz.

    Args:
        param1: Descrição do parâmetro.
        opcional: Parâmetro opcional.
    """
    return _minha_funcao(param1, opcional)

if __name__ == "__main__":
    mcp.run()
```

### 2.6 Passo 5: Escrever Testes

```python
# mcps/meu-servico/tests/test_smoke.py
# REGRA: Testar core.py, NÃO server.py (server.py precisa de mcp instalado)
# REGRA: Mínimo 3~5 testes por função

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core import minha_funcao


def test_minha_funcao_basico():
    """Cenário feliz."""
    result = minha_funcao("teste")
    assert "resultado" in result
    assert "Processado: teste" in result["resultado"]


def test_minha_funcao_com_opcional():
    """Com parâmetro opcional."""
    result = minha_funcao("teste", opcional="extra")
    assert result["resultado"] is not None


def test_minha_funcao_tem_timestamp():
    """Sempre retorna timestamp."""
    result = minha_funcao("teste")
    assert "timestamp" in result
    assert "T" in result["timestamp"]  # ISO 8601


def test_minha_funcao_vazio():
    """String vazia como input."""
    result = minha_funcao("")
    assert result["resultado"] is not None
```

### 2.7 Passo 6: Validar (verify-mcp — 15 checks)

```bash
python3 scripts/verify-mcp.py meu-servico
```

**Resultado esperado:**

```
============================================================
  VERIFICANDO: meu-servico
============================================================
  (checks passando...)
  ✅ APROVADO — 15 checks, 0 erros
```

**Se falhar:** corrigir cada erro apontado antes de prosseguir.

### 2.8 Passo 7: Atualizar Lockfile

```bash
python3 -c "
from catalog import list_mcp_ids, read_manifest, manifest_hash, read_lockfile, write_lockfile
lock = read_lockfile()
if 'entries' not in lock: lock['entries'] = {}
for mid in list_mcp_ids():
    man = read_manifest(mid)
    if man:
        lock['entries'][mid] = {
            'version': man.get('version','0.0.0'),
            'manifest_hash': manifest_hash(mid) or '',
            'deps_hash': ''
        }
write_lockfile(lock)
print('Lockfile atualizado')
"
```

**IMPORTANTE:** O lockfile contém o **SHA-256** de cada `mcp.json`. A **cache key** é derivada do lockfile inteiro. Se o lockfile não for atualizado, o cache key fica desatualizado e o snapshot não reflete o novo estado.

### 2.9 Passo 8: Testar Dispatch (event-driven)

```bash
# Disparar APENAS seu MCP
gh workflow run mcp-runtime.yml -f mcp_id=meu-servico --repo camillanapoles/mcps-as-objects

# Acompanhar
gh run view <run-id> --repo camillanapoles/mcps-as-objects --watch
```

### 2.10 Passo 9: Commitar

```bash
git add mcps/meu-servico/ mcps-lock.json
git commit -m "feat: novo MCP meu-servico — <descrição>"
git push
```

---

## ═══════════════════════════════════════════════════════════════
## PARTE 3 — O QUE VAI NO DB (SQLite)
## ═══════════════════════════════════════════════════════════════

### 3.1 Estrutura do Banco

```sql
-- Tabela: mcps
-- Um registro por MCP. Preenchido automaticamente por register_mcp().
mcps (
    id TEXT PRIMARY KEY,           -- kebab-case (ex: "meu-servico")
    name TEXT NOT NULL,            -- Nome amigável
    version TEXT NOT NULL,         -- semver
    description TEXT,              -- Descrição do MCP
    manifest_path TEXT NOT NULL,   -- Caminho do mcp.json
    manifest_hash TEXT NOT NULL,   -- SHA-256 do mcp.json
    registered_at TIMESTAMP,       -- Quando foi registrado
    updated_at TIMESTAMP           -- Última atualização
)

-- Tabela: functions
-- Uma linha por função declarada no manifesto.
functions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mcp_id TEXT NOT NULL,          -- FK → mcps.id
    name TEXT NOT NULL,            -- snake_case
    description TEXT,
    input_schema TEXT,             -- JSON Schema (em texto)
    output_schema TEXT,            -- JSON Schema (em texto)
    UNIQUE (mcp_id, name)
)

-- Tabela: runs
-- Histórico de execuções.
runs (
    id TEXT PRIMARY KEY,           -- UUID
    mcp_id TEXT NOT NULL,
    function_name TEXT NOT NULL,
    input_payload TEXT,            -- JSON
    output_payload TEXT,           -- JSON
    status TEXT CHECK(status IN ('pending','ok','error')),
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    workflow_run_id TEXT
)
```

### 3.2 Como Popular o DB

```bash
# Escanear filesystem e registrar TODOS os MCPs
python3 -c "
from db import get_conn
from crud import scan_and_register_all
conn = get_conn()
count = scan_and_register_all(conn)
print(f'{count} MCPs registrados')
"
```

### 3.3 Como Consultar o DB

```bash
python3 -c "
from db import get_conn
from crud import list_mcps, get_mcp
conn = get_conn()

# Listar todos
for m in list_mcps(conn):
    print(f'{m[\"id\"]} v{m[\"version\"]} — {m[\"description\"][:50]}')

# Pegar um específico
m = get_mcp(conn, 'example-greeter')
print(m)
"
```

---

## ═══════════════════════════════════════════════════════════════
## PARTE 4 — TESTES
## ═══════════════════════════════════════════════════════════════

### 4.1 Onde Colocar os Testes

```
mcps/<id>/tests/
└── test_smoke.py    ← Testes do core.py (obrigatório)

registry/tests/
└── test_smoke.py    ← Testes do registry (back-end)
```

### 4.2 Regras dos Testes

| Regra | Motivo |
|-------|--------|
| **Testar `core.py`, NUNCA `server.py`** | `server.py` importa `mcp` SDK que pode não estar instalado no ambiente de teste (ex: Termux sem `pydantic-core`) |
| **Usar só stdlib nos imports do teste** | Evita dependências não disponíveis |
| **Mínimo 1 teste por função pública** | Cobertura básica |
| **Nome descritivo** | `test_minha_funcao_quando_x()` |
| **Testar bordas** | String vazia, None, valores extremos |

### 4.3 Como Rodar os Testes

```bash
# Testes de um MCP específico
python3 -m pytest mcps/meu-servico/tests/ -v

# Testes do registry
python3 -m pytest registry/tests/ -v

# Todos os testes
python3 -m pytest mcps/*/tests/ registry/tests/ -v

# Sem pytest (usando unittest)
python3 -c "
import sys, unittest
sys.path.insert(0, 'mcps/meu-servico/tests')
sys.path.insert(0, 'mcps/meu-servico/src')
from test_smoke import *
loader = unittest.TestLoader()
suite = loader.loadTestsFromModule(sys.modules['test_smoke'])
runner = unittest.TextTestRunner(verbosity=2)
runner.run(suite)
"
```

### 4.4 Estrutura de Teste Ideal

```python
"""
Testes de fumaça para meu-servico.
Testa core.py diretamente (sem depender do MCP SDK).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core import minha_funcao, outra_funcao


# ── Cenários felizes ──────────────────────────────────

def test_minha_funcao_basico():
    """Funciona com parâmetros mínimos."""
    r = minha_funcao("teste")
    assert r["resultado"] == "esperado"


# ── Cenários de borda ─────────────────────────────────

def test_minha_funcao_vazio():
    """Input vazio não quebra."""
    r = minha_funcao("")
    assert r is not None


# ── Validação de schema de saída ──────────────────────

def test_minha_funcao_tem_campos_obrigatorios():
    """Output sempre tem os campos esperados."""
    r = minha_funcao("x")
    assert all(k in r for k in ["resultado", "timestamp"])
```

---

## ═══════════════════════════════════════════════════════════════
## PARTE 5 — COMO EDITAR UM MCP EXISTENTE
## ═══════════════════════════════════════════════════════════════

### 5.1 Fluxo de Edição

```
1. Identificar o que mudar
2. Editar arquivo(s)
3. Validar (verify-mcp)
4. Atualizar lockfile
5. Rodar testes
6. Commitar (mcp.json + mcps-lock.json juntos)
```

### 5.2 Cenários Comuns de Edição

| O que mudar | Onde editar | Verificar |
|-------------|-------------|-----------|
| Adicionar função | `mcp.json` + `core.py` + `server.py` + `tests/` | `verify-mcp` + testes |
| Remover função | `mcp.json` + `core.py` + `server.py` + `tests/` | `verify-mcp` |
| Mudar input/output schema | `mcp.json` + `core.py` + `server.py` + `tests/` | Schema validation |
| Corrigir descrição | `mcp.json` | `verify-mcp` |
| Mudar plataforma | `mcp.json` (campo `platforms`) | `verify-mcp` |
| Adicionar dependência | `requirements.txt` (se existir) | Testes |
| Corrigir bug na lógica | `core.py` | Testes |

### 5.3 Regras de Edição

```
╔══════════════════════════════════════════════════════════════════╗
║  SEMPRE editar mcp.json e mcps-lock.json no MESMO commit       ║
║  NUNCA deixar o lockfile desatualizado                         ║
║  SEMPRE rodar verify-mcp <id> antes de commitar                ║
║  NUNCA editar server.py sem antes verificar core.py            ║
║  SEMPRE atualizar testes se a lógica mudou                     ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## ═══════════════════════════════════════════════════════════════
## PARTE 6 — ARQUITETURA DE DECISÃO (LOCAL vs REMOTO)
## ═══════════════════════════════════════════════════════════════

### 6.1 Como Decidir

```
Sua nova funcionalidade:
│
├─ Leva <1s, não precisa de toolchain?
│  → LOCAL (stdio via server.py / HTTP via API)
│  → Responde em ms, pi-agent consegue chamar
│
├─ Leva >1s, precisa de build/compilação?
│  → REMOTO (GitHub Actions workflow)
│  → Responde em minutos, dispatch via gh ou API
│
├─ Ambos?
│  → Lógica em core.py
│  → server.py para LOCAL
│  → workflow para REMOTO
```

### 6.2 Exemplos do Próprio Projeto

| MCP | LOCAL | REMOTO |
|-----|-------|--------|
| `example-greeter` | `greet()` 10ms | ❌ (não faz sentido) |
| `python-termux-builder` | `check_package()` 50ms | `build_wheel()` 3min |
| `processador-texto` | `exemplo()` 5ms | ❌ (não faz sentido) |

---

## ═══════════════════════════════════════════════════════════════
## PARTE 7 — REGRAS DE OURO (RESUMO)
## ═══════════════════════════════════════════════════════════════

```
┌────────────────────────────────────────────────────────────────┐
│  📌 SEMPRE                                                      │
│  ├─ Rodar verify-mcp antes de commitar                         │
│  ├─ Atualizar lockfile junto com mcp.json                      │
│  ├─ Testar core.py (nunca server.py)                           │
│  └─ Usar scripts/ em vez de Python inline em YAML              │
│                                                                │
│  🚫 NUNCA                                                       │
│  ├─ Colocar lógica em server.py (vai pra core.py)              │
│  ├─ Esquecer --repo no gh workflow run                         │
│  ├─ Usar description= ou version= em FastMCP()                │
│  └─ Commitar mcp.json sem mcps-lock.json                       │
│                                                                │
│  ⚠️ CUIDADO                                                     │
│  ├─ YAML + Python multiline → sempre usar scripts/             │
│  ├─ db.py vs platdetect.py → stdlib platform tem name clash   │
│  └─ FastMCP API mudou → v1.28+ só aceita name                │
└────────────────────────────────────────────────────────────────┘
```

---

## ═══════════════════════════════════════════════════════════════
## PARTE 8 — CHECKLIST RÁPIDO PARA QUALQUER AÇÃO
## ═══════════════════════════════════════════════════════════════

```
□ Entendi o estado atual do repositório (git status + git log)
□ Se é novo MCP → segui o passo a passo da Parte 2
□ Se é edição → segui o fluxo da Parte 5
□ Manifesto válido (verify-mcp)
□ Lockfile atualizado (mcps-lock.json)
□ Testes passam (pytest)
□ Commit inclui mcp.json + mcps-lock.json juntos
□ Dispatch funciona (gh workflow run -f mcp_id=<id>)
```

---

## ═══════════════════════════════════════════════════════════════
## PARTE 9 — REFERÊNCIA RÁPIDA
## ═══════════════════════════════════════════════════════════════

```bash
# 🆕 Criar MCP
python3 -c "from constructor import create_mcp; create_mcp('id', name='Nome', description='Desc')"

# ✅ Verificar MCP
python3 scripts/verify-mcp.py <id>
python3 scripts/verify-mcp.py --all

# 📦 Atualizar lockfile
python3 -c "from catalog import *; lock = read_lockfile(); [...] write_lockfile(lock)"

# 🧪 Rodar testes
python3 -m pytest mcps/<id>/tests/ -v

# 📋 Listar MCPs
python3 scripts/list-mcps.py

# 🚀 Disparar workflow individual
gh workflow run mcp-runtime.yml -f mcp_id=<id> --repo camillanapoles/mcps-as-objects

# 🌐 API local
uvicorn registry.src.api:app --host 127.0.0.1 --port 8712

# 🔑 Ver cache key
python3 scripts/compute-key.py

# 📊 Ver plataforma
curl http://127.0.0.1:8712/platform
```
