# 📜 Governance — mcps-as-objects

> **Propósito**: Definir as regras, ciclos e responsabilidades para que todo MCP no ecossistema seja determinístico, rastreável, isolado e replicável.

---

## 1. Princípios

| Princípio | Descrição |
|-----------|-----------|
| **Determinismo** | Mesmo input + mesmo manifesto = mesmo output. Cache key deriva de SHA-256 do lockfile. |
| **Isolamento** | Cada MCP é um objeto independente. Seu workflow não interfere em outros MCPs. |
| **Verificação obrigatória** | Todo MCP novo ou modificado passa por 15 checks de conformidade antes de ser aceito. |
| **Cache inviolável** | A chave de cache inclui SHA-256 de todo o lockfile. Qualquer mudança no manifesto → cache key diferente → snapshot anterior não contamina. |
| **Event-driven** | Cada MCP responde ao seu próprio evento de chamada. Nenhum MCP é executado sem ser explicitamente invocado. |
| **Plataforma explícita** | Todo MCP declara em quais plataformas funciona. O registry filtra automaticamente. |
| **Schema-first** | O manifesto `mcp.json` é a única fonte da verdade. Tudo mais deriva dele. |

---

## 2. Ciclo de Vida de um MCP

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Criação │────▶│  Pré-    │────▶│  Lock    │────▶│  Registro│────▶│  Runtime │
│(template)│     │  staging │     │(SHA-256) │     │  (DB)    │     │(workflow)│
└──────────┘     └──────────┘     └──────────┘     └──────────┘     └──────────┘
                       │
                       ▼
                 ┌──────────┐
                 │ Verify   │
                 │ 15 checks│
                 └──────────┘
```

### 2.1 Fases

| Fase | Ação | Quem | Gate |
|------|------|------|------|
| **Criação** | `mcpsctl new <id>` ou `constructor.create_mcp()` | Dev / CLI | ID válido (kebab-case) |
| **Pré-staging** | `verify-mcp.py <id>` — 15 checks automáticos | CI / CLI | 0 erros |
| **Lock** | `mcpsctl lock` — atualiza SHA-256 no lockfile | Dev / CI | Hash condiz com manifesto |
| **Registro** | `register_mcp()` — persiste no SQLite | Registry | Entrada no lockfile |
| **Runtime** | `gh workflow run mcp-runtime.yml -f mcp_id=<id>` | Usuário / API | MCP compatível com plataforma |

### 2.2 Rollback

Se um MCP quebrar em runtime:
1. Reverte o `mcp.json` para versão anterior
2. Reexecuta `mcpsctl lock` → cache key volta para o hash anterior
3. O snapshot anterior (ainda em cache) é restaurado automaticamente
4. O MCP volta a funcionar sem rebuild

---

## 3. Regras de Verificação (15 Checks)

| # | Check | Obrigatório | Falha bloqueia? |
|---|-------|------------|-----------------|
| 1 | 📁 Estrutura de diretórios (`mcp.json`, `src/server.py`) | Sim | Sim |
| 2 | 📁 Nomenclatura (kebab-case) | Sim | Sim |
| 3 | 📜 Manifesto JSON válido | Sim | Sim |
| 4 | 📜 Contra schema (`mcp-manifest.schema.json`) | Sim | Sim |
| 5 | 📜 `id` condiz com diretório | Sim | Sim |
| 6 | 📜 `platforms` definido | Não | Warning |
| 7 | 📜 Ao menos 1 função | Sim | Sim |
| 8 | 🔧 Entrypoint existe | Sim | Sim |
| 9 | 🔧 `@mcp.tool()` condizentes com manifesto | Sim | Sim |
| 10 | 🧪 Testes existem | Não | Warning |
| 11 | 🧪 Testes compilam | Não | Warning |
| 12 | 📦 Entrada no lockfile | Sim | Warning |
| 13 | 💾 Cache: SHA-256 do lockfile | Sim | Warning |
| 14 | 🚀 Pode ser disparado individualmente | Sim | Sim |
| 15 | 📱 Plataforma válida | Não | Warning |

---

## 4. Controle de Cache e Isolamento

### 4.1 Chave de Cache

```
cache_key = "mcp-snapshot-v1-{sha256(mcps-lock.json)}-{sha256(uname)[:12]}"
```

- **SHA-256 do lockfile inteiro** → qualquer alteração em QUALQUER MCP invalida o cache
- **SHA-256 do uname** → ambientes diferentes têm caches diferentes
- **Prefixo v1** → permite migração de formato de cache

### 4.2 Política de Isolamento

- Cada lockfile hash → um snapshot único
- MCPs diferentes → lockfile diferente → cache key diferente → sem contaminação
- Se o lockfile não mudou entre execuções → cache hit → restaura em segundos
- Se o lockfile mudou → cache miss → novo snapshot construído do zero

### 4.3 O que vai no cache

```
.cache/snapshot/
├── .venv/                    # Dependências Python (pip)
├── registry/data/registry.db # Estado do SQLite
└── mcps-lock.json            # Fingerprint (para verificação)
```

---

## 5. Plataformas

### 5.1 Taxonomia

| String | Descrição |
|--------|-----------|
| `*` | Qualquer plataforma (MCP universal) |
| `linux/amd64` | GitHub Actions runner, Ubuntu amd64 |
| `linux/arm64` | ARM64 Linux |
| `android/termux` | Termux no Android (aarch64) |
| `darwin/amd64` | macOS Intel |
| `darwin/arm64` | macOS Apple Silicon |

### 5.2 Regras de Filtro

1. Se MCP declara `["*"]` → disponível em todas as plataformas
2. Se MCP declara `["android/termux"]` → disponível **apenas** em Termux
3. O registry detecta a plataforma atual via `platdetect.detect_platform()`
4. `GET /mcps/compatible` retorna apenas MCPs compatíveis
5. `POST /mcps/{id}/dispatch` bloqueia se incompatível (HTTP 400)

---

## 6. Event-Driven

### 6.1 Princípio

Cada MCP é um **objeto** com seu próprio ciclo de vida. Nenhuma execução acontece sem um evento explícito:

```
Evento                          Ação
────────────────────────────────────────────────────────────
workflow_dispatch               gh workflow run mcp-runtime.yml -f mcp_id=<id>
POST /mcps/{id}/dispatch        API → gh workflow run
CRON / schedule                  Workflow schedule (futuro)
Chain (pipeline)                 Output de MCP A → input de MCP B
```

### 6.2 Isolamento de Execução

- Um workflow executando `mcp_id=X` NÃO executa `mcp_id=Y`
- Cada worker job tem seu próprio runner (máquina isolada)
- Falha em um MCP não afeta outros

---

## 7. CI/CD

### 7.1 Workflows

| Workflow | Trigger | O que faz |
|----------|---------|-----------|
| `mcp-validate.yml` | PR com mudanças em `mcps/` | Valida manifestos contra schema + lockfile |
| `mcp-verify.yml` | PR com mudanças em `mcps/` | Executa `verify-mcp.py --all` (15 checks) |
| `mcp-cache.yml` | Schedule + push em `mcps-lock.json` | Reconstrói snapshot de cache |
| `mcp-runtime.yml` | `workflow_dispatch` | Executa MCP(s) em produção |
| `mcp-single.yml` | `workflow_dispatch` (input `mcp_id`) | Executa 1 MCP específico |

### 7.2 Regras de Aprovação

| Situação | Ação |
|----------|------|
| PR com MCP novo | `mcp-verify.yml` precisa passar |
| PR modificando manifesto | `mcp-validate.yml` precisa passar |
| Falha no verify | PR bloqueado, comentário automático |
| Lockfile desatualizado | Warning no verify, corrigir antes do merge |

---

## 8. Versionamento

- `mcps/<id>/mcp.json` contém `version` (semver)
- Lockfile armazena `version` + `manifest_hash` (SHA-256 do mcp.json)
- Tags Git seguem `mcp-<id>-<version>` (ex: `mcp-python-termux-builder-0.1.0`)
- Cache key NÃO inclui version, apenas hash — evita recache desnecessário

---

## 9. Responsabilidades

| Papel | Responsabilidade |
|-------|-----------------|
| **Registry** | Catalogar, validar, registrar, prover API e MCP server |
| **Constructor** | Materializar novos MCPs a partir do template |
| **Verifier** | Garantir conformidade com 15 checks |
| **Workflows** | Executar MCPs em runtime, gerenciar cache |
| **Platdetect** | Detectar plataforma, filtrar MCPs compatíveis |
| **pi-coding-agent** | Consumidor externo via MCP protocol (stdio) |

---

## 10. Boas Práticas

1. **Nunca edite `mcp.json` manualmente sem rodar `mcpsctl lock` depois**
2. **Sempre valide antes de commitar**: `python3 scripts/verify-mcp.py <id>`
3. **MCP específico de plataforma** deve declarar `platforms` explicitamente
4. **Cache hit** reduz execução de ~3min para ~5s — mantenha lockfile atualizado
5. **Erro no verify** não é opcional — corrija antes de prosseguir
6. **Testes** devem testar a lógica em `core.py` (sem depender do MCP SDK)
