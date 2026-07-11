# 🏗️ MCPs as Objects — Gestão Determinística de MCPs

```
┌────────────────────────────────────────────────────┐
│  GESTÃO MCPS AS A OBJECT                           │
│  └─ ESTRUTURA GERENCIADA                           │
│  └─ CONTROLE RÍGIDO DE PATTERN E NOMENCLATURA      │
│  └─ DETERMINÍSTICO                                 │
│  └─ RUNTIME EM GITHUB WORKFLOW CACHE/SNAPSHOT      │
│  └─ BACKEND + SQLITE + API                         │
│  └─ CATÁLOGO: descrição, funções, input, output     │
│  └─ CRIADOR DE MCPS CONFORME PADRÃO                │
│  └─ CADA MCP É UMA MÁQUINA ISOLADA                 │
└────────────────────────────────────────────────────┘
```

**mcps-as-objects** é um sistema determinístico para criar, catalogar, validar, executar e compor **MCPs (Model Context Protocol servers)** como objetos gerenciados, rodando em runtime no **GitHub Actions** com cache inteligente via snapshot.

---

## ✨ Filosofia

1. **Tudo é gerenciado** — Não existem MCPs soltos. Todo MCP tem um manifesto, um schema, um ciclo de vida.
2. **Padrão único e rígido** — Estrutura de diretórios, nomenclaturas e versões seguem um contrato determinístico.
3. **Máquinas isoladas** — Cada MCP roda em seu próprio job/sandbox no GitHub Actions.
4. **Pipeline modular** — MCPs se compõem: output de um vira input de outro.
5. **Cache inteligente** — Snapshot da máquina montada (venv + DB + lockfile) é restaurado em segundos.
6. **Replicável** — `git clone` + `bootstrap.sh` = tudo funcionando, e criar um novo MCP é um comando.

---

## 🚀 Quickstart (5 minutos)

```bash
# 1. Clone e entre
git clone <seu-repo> && cd mcps-as-objects

# 2. Bootstrap (instala deps, valida, mostra comandos)
./tools/bootstrap.sh

# 3. Crie seu primeiro MCP
./tools/mcpsctl new meu-mcp --name "Meu MCP" --desc "Faz algo incrível"

# 4. Edite o manifesto
#    vim mcps/meu-mcp/mcp.json

# 5. Implemente o servidor
#    vim mcps/meu-mcp/src/server.py

# 6. Valide
./tools/mcpsctl validate meu-mcp

# 7. Atualize lockfile
./tools/mcpsctl lock

# 8. Suba a API e teste
make run-api
# curl http://127.0.0.1:8712/mcps
```

---

## 📁 Estrutura do Projeto

```
mcps-as-objects/
├── .github/workflows/         # Workflows GitHub Actions
│   ├── mcp-runtime.yml        # 🏭 Pipeline principal (matrix)
│   ├── mcp-cache.yml          # 💾 Build de snapshot
│   └── mcp-validate.yml       # ✅ CI validação
│
├── schemas/                   # 📐 Fonte da verdade (JSON Schema)
│   ├── mcp-manifest.schema.json
│   ├── function-io.schema.json
│   └── lockfile.schema.json
│
├── mcps/                      # 📦 MCPs catalogados
│   ├── _template/             #     Template determinístico
│   └── example-greeter/       #     Exemplo funcional
│
├── registry/                  # ⚙️ Registry Backend
│   ├── src/
│   │   ├── server.py          #     MCP server (stdio)
│   │   ├── api.py             #     HTTP API (FastAPI)
│   │   ├── cli.py             #     CLI (mcpsctl)
│   │   ├── db.py              #     SQLite + migrations
│   │   ├── crud.py            #     CRUD operations
│   │   ├── catalog.py         #     Leitura de manifestos
│   │   ├── validator.py       #     Validação contra schemas
│   │   ├── constructor.py     #     Criador de MCPs (template)
│   │   ├── composer.py        #     Pipeline/composição
│   │   └── snapshot.py        #     Cache key determinística
│   ├── data/
│   └── tests/
│
├── tools/                     # 🔧 Ferramentas
│   ├── mcpsctl                #     CLI principal
│   ├── bootstrap.sh           #     Setup inicial
│   └── snapshot.sh            #     Cache helpers
│
├── docs/                      # 📖 Documentação
│   ├── ARCHITECTURE.md
│   ├── PATTERNS.md
│   ├── MCP-AUTHORING.md
│   └── WORKFLOW-RUNTIME.md
│
├── mcps-lock.json             # 📌 Lockfile determinístico
├── requirements.txt
├── Makefile
└── README.md
```

---

## 🎮 Comandos

### CLI (`tools/mcpsctl`)

| Comando | Descrição |
|---------|-----------|
| `list` | Listar MCPs catalogados |
| `describe <id>` | Detalhar um MCP (manifesto completo) |
| `new <id>` | **Criar novo MCP** a partir do template |
| `validate <id>` ou `--all` | Validar manifesto(s) contra schemas |
| `lock` | Atualizar `mcps-lock.json` com hashes |
| `scan` | Escanear filesystem e registrar no DB |
| `serve-api` | Rodar API HTTP (porta 8712) |
| `serve-mcp` | Rodar MCP server (stdio) |
| `cache-key` | Mostrar chave de cache determinística |

### Make

| Alvo | Descrição |
|------|-----------|
| `make install` | Virtualenv + dependências |
| `make run-api` | API HTTP em :8712 |
| `make run-mcp` | MCP server stdio |
| `make validate` | Validar todos os manifestos |
| `make test` | Rodar testes |
| `make lock` | Atualizar lockfile |
| `make new id=<id>` | Criar novo MCP |

---

## 💡 Criar um Novo MCP (passo a passo)

```bash
# 1. Cria estrutura a partir do template
tools/mcpsctl new meu-data-processor

# 2. Edita manifesto
vim mcps/meu-data-processor/mcp.json

# 3. Implementa
vim mcps/meu-data-processor/src/server.py

# 4. Valida
tools/mcpsctl validate meu-data-processor

# 5. Lock
tools/mcpsctl lock

# 6. Testa via API (com make run-api rodando)
curl -X POST http://127.0.0.1:8712/mcps/meu-data-processor/run \
  -H "Content-Type: application/json" \
  -d '{"function_name": "minha_funcao", "input_payload": {"arg": "valor"}}'

# 7. Commita e faz PR → CI valida automaticamente
```

---

## 🔄 Como o Runtime Funciona (GitHub Actions)

1. **Cache hit** → `.venv` + `registry.db` restaurados em <1s
2. **Cache miss** → Instala deps, constrói DB, salva snapshot
3. **Registry boot** → API sobe, cataloga todos MCPs
4. **Matrix workers** → Cada MCP roda em job isolado
5. **Collect** → Resultados consolidados em artifact

[Leia mais →](docs/WORKFLOW-RUNTIME.md)

---

## 📐 Determinismo

| Aspecto | Garantia |
|---------|----------|
| Cache key | `sha256(mcps-lock.json)` + `sha256(uname -a)` |
| Manifesto | Schema único, validação dupla (CI + runtime) |
| Output | Dado mesmo input + mesmo snapshot = mesmo output |
| Snapshot | Imutável até lockfile mudar |
| Pipeline | DAG topológica sem efeitos colaterais |

---

## 🔗 Integração com pi-coding

O registry expõe um **MCP server via stdio** que o `pi-coding-agent` pode consumir:

```jsonc
// .pi/config.json ou mcpServers do pi
{
  "mcps-as-objects": {
    "command": "python3",
    "args": ["registry/src/server.py"],
    "cwd": "/caminho/mcps-as-objects"
  }
}
```

Isso permite que o pi consulte o catálogo, descreva MCPs, valide manifestos e até crie novos MCPs — tudo via chat.

---

## 🧪 Testes

```bash
make test
# Ou
python3 -m pytest -v registry/tests/ mcps/example-greeter/tests/
```

---

## 📖 Documentação

| Documento | Leituras |
|-----------|----------|
| [Arquitetura](docs/ARCHITECTURE.md) | Visão geral do sistema, camadas, princípios |
| [Critérios de Uso](docs/CRITERIA.md) | ⚡ Quando usar LOCAL (stdio) vs REMOTO (GitHub Actions) |
| [Governança](docs/GOVERNANCE.md) | 📜 Regras, ciclos, verificações e responsabilidades |
| [Projeto](docs/PROJECT.md) | 🏗️ Documento vivo — arquitetura completa, fluxos, componentes |
| [Patterns](docs/PATTERNS.md) | **Regras rígidas** de nomenclatura e estrutura |
| [Authoring](docs/MCP-AUTHORING.md) | Guia prático: como criar um novo MCP |
| [Workflow Runtime](docs/WORKFLOW-RUNTIME.md) | Como executa em GitHub Actions |
