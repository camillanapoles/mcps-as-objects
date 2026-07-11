# 📋 Checklist de Execução — Integração mcp-builder → mcps-as-objects

> **Registro de execução replicável.** Este documento serve como guia passo a passo
> para implementar a integração E como template para futuros projetos.

---

## ═══════════════════════════════════════════════════════════════════
## 0. PREPARAÇÃO DO AMBIENTE
## ═══════════════════════════════════════════════════════════════════

### 0.1 Pré-requisitos

```
□ Git configurado (git config --global user.name / email)
□ GitHub CLI autenticado (gh auth status)
□ Python 3.11+ instalado
□ Node.js 18+ instalado (para mcp-builder)
□ Acesso ao repositório camillanapoles/mcps-as-objects
□ Acesso ao repositório camillanapoles/mcp-builder
```

### 0.2 Branches

```
□ Branch base: main (mcps-as-objects)
□ Branch de trabalho: feat/pi-ecosystem-management
□ mcp-builder: branch main ou release
```

---

## ═══════════════════════════════════════════════════════════════════
## 1. CRIAR O GITHUB PROJECT (KANBAN)
## ═══════════════════════════════════════════════════════════════════

### 1.1 Criar o Project

```bash
gh project create "Integração mcp-builder ↔ mcps-as-objects" \
  --org camillanapoles \
  --description "Bridge entre mcp-builder e mcps-as-objects: adapter + templates + hooks + fsm"
```

### 1.2 Configurar Colunas

```
Colunas do Kanban:
  📋 Backlog    → Issues priorizadas
  🏗️ Doing      → Em execução
  ✅ Review     → PR aberto
  🚀 Staging   → Testado em CI
  📦 Done       → Fechado
```

### 1.3 Criar Labels

```bash
gh label create fase-1-adapter --color 0052cc  --description "Adapter core"
gh label create fase-2-templates --color 008672 --description "Templates complementares"
gh label create fase-3-hooks --color d93f0b --description "Hook pós-scaffold"
gh label create fase-4-fsm --color 5319e7 --description "FSM + Blueprint + Registry"
gh label create fase-5-governanca --color b60205 --description "Hooks de governança"
gh label create compliance --color ffea82 --description "Zero hardcoded / gerenciado / agnóstico"
gh label create bug --color d73a4a --description "Erro"
gh label create test --color 28a745 --description "Testes"
gh label create docs --color 6f42c1 --description "Documentação"
```

### 1.4 Criar Milestones

```bash
gh api repos/camillanapoles/mcps-as-objects/milestones \
  -f title="M1 — Bridge Funcional" \
  -f description="Fase 1+2: adapter.ingest() + templates" \
  -f due_on="2026-08-01T00:00:00Z"

gh api repos/camillanapoles/mcps-as-objects/milestones \
  -f title="M2 — Integração Automática" \
  -f description="Fase 3: hook pós-scaffold"

gh api repos/camillanapoles/mcps-as-objects/milestones \
  -f title="M3 — Unificação" \
  -f description="Fase 4: FSM + Blueprint + Registry"

gh api repos/camillanapoles/mcps-as-objects/milestones \
  -f title="M4 — Governança" \
  -f description="Fase 5: hooks cross-platform"
```

---

## ═══════════════════════════════════════════════════════════════════
## 2. ABRIR AS ISSUES (10 CARDS)
## ═══════════════════════════════════════════════════════════════════

### 2.1 Card 1.1 — adapter.ingest() core

```bash
gh issue create \
  --title "[FASE-1] adapter.ingest() — ler blueprint.yaml e gerar mcp.json" \
  --label fase-1-adapter,compliance \
  --milestone "M1 — Bridge Funcional" \
  --body '
## Descrição
Implementar adapter.ingest() que lê blueprint.yaml do mcp-builder e gera mcp.json compatível com mcps-as-objects.

## Critérios de Validação
- [ ] Código implementado em registry/src/adapter.py
- [ ] adapter.ingest("mcps/example-greeter") → mcp.json idêntico ao original
- [ ] adapter.ingest() → verify-mcp passa (0 erros)
- [ ] adapter.ingest() → lockfile atualizado
- [ ] adapter.ingest() → DB tem o MCP registrado
- [ ] Zero hardcoded: blueprint.yaml é a única fonte

## Compliance
- [ ] Zero hardcoded (sem string fixa do nome do MCP)
- [ ] Gerenciado (DB + lockfile + verify)
- [ ] Agnóstico (funciona com Python, TS, Go, Rust)
- [ ] Testado (testes no adapter)
'
```

### 2.2 Card 1.2 — adapter.info() e adapter.sync()

```bash
gh issue create \
  --title "[FASE-1] adapter.info() e adapter.sync() — consulta e atualização" \
  --label fase-1-adapter \
  --milestone "M1 — Bridge Funcional" \
  --body '
## Descrição
Implementar adapter.info() que retorna dados consolidados (manifesto + FSM + runs) e adapter.sync() que revalida se blueprint mudou.

## Critérios de Validação
- [ ] adapter.info("example-greeter") → manifesto + FSM + runs
- [ ] adapter.sync("example-greeter") → revalida, relock, re-registra
- [ ] Se nada mudou, sync é no-op
- [ ] Se algo mudou e quebrou verify, sync retorna erro
'
```

### 2.3 Card 1.3 — Testes do adapter

```bash
gh issue create \
  --title "[FASE-1] Testes do adapter (15 testes)" \
  --label fase-1-adapter,test \
  --milestone "M1 — Bridge Funcional" \
  --body '
## Descrição
Criar testes unitários e de integração para o adapter.

## Testes Requeridos
- [ ] test_ingest_example_greeter()
- [ ] test_ingest_novo_mcp()
- [ ] test_ingest_sem_blueprint()
- [ ] test_ingest_sdk_python()
- [ ] test_ingest_sdk_typescript()
- [ ] test_ingest_sdk_go()
- [ ] test_ingest_sdk_rust()
- [ ] test_ingest_pattern_stateless()
- [ ] test_ingest_pattern_event()
- [ ] test_ingest_pattern_factory()
- [ ] test_info()
- [ ] test_sync_sem_mudanca()
- [ ] test_sync_com_mudanca()
- [ ] test_sync_quebra_verify()
- [ ] Zero hardcoded: nenhum nome fixo (usa parametrize)
'
```

### 2.4 Card 2.1 — Template mcp.json.hbs

```bash
gh issue create \
  --title "[FASE-2] Template mcp.json.hbs (12 arquivos, 4 SDKs × 3 patterns)" \
  --label fase-2-templates \
  --milestone "M1 — Bridge Funcional" \
  --body '
## Descrição
Criar templates mcp.json.hbs para todos os 12 slots do mcp-builder.

## Arquivos
- templates/python-sdk/stateless/mcp.json.hbs
- templates/python-sdk/event/mcp.json.hbs
- templates/python-sdk/factory/mcp.json.hbs
- templates/typescript-sdk/stateless/mcp.json.hbs
- templates/typescript-sdk/event/mcp.json.hbs
- templates/typescript-sdk/factory/mcp.json.hbs
- templates/go-sdk/stateless/mcp.json.hbs
- templates/go-sdk/event/mcp.json.hbs
- templates/go-sdk/factory/mcp.json.hbs
- templates/rust-sdk/stateless/mcp.json.hbs
- templates/rust-sdk/event/mcp.json.hbs
- templates/rust-sdk/factory/mcp.json.hbs

## Validação
- [ ] npx mcp-builder new x --sdk python --pattern stateless → gera mcp.json válido
- [ ] Schema validation passa
- [ ] blueprint.sdk e blueprint.pattern corretos
'
```

### 2.5 Card 2.2 — Template server.py.hbs

```bash
gh issue create \
  --title "[FASE-2] Template server.py.hbs (FastMCP wrapper Python)" \
  --label fase-2-templates \
  --milestone "M1 — Bridge Funcional" \
  --body '
## Descrição
Template Handlebars para gerar server.py com FastMCP wrapper.

## Validação
- [ ] Gera src/server.py com FastMCP(name=...)
- [ ] Gera @mcp.tool() para cada tool
- [ ] Importa de core (lógica pura)
- [ ] verify-mcp passa
- [ ] python src/server.py inicia sem erro
'
```

### 2.6 Card 3.1 — Hook post-scaffold

```bash
gh issue create \
  --title "[FASE-3] Hook post-scaffold — chama adapter.ingest automaticamente" \
  --label fase-3-hooks \
  --milestone "M2 — Integração Automática" \
  --body '
## Descrição
Hook que dispara adapter.ingest() automaticamente após mcp-builder gerar um projeto.

## Validação
- [ ] mcp-builder new x → hook dispara
- [ ] Hook chama adapter.ingest() com path correto
- [ ] Se adapter ok → hook ok
- [ ] Se adapter erro → hook bloqueia (gate)
- [ ] Mensagem de erro com sugestões
'
```

### 2.7 Card 4.1 — FSM no Registry

```bash
gh issue create \
  --title "[FASE-4] FSM Engine integrada ao Registry" \
  --label fase-4-fsm \
  --milestone "M3 — Unificação" \
  --body '
## Descrição
Integrar FSM do mcp-builder no Registry: ler .mcp/state/ e expor via API.

## Endpoints
- GET /mcps/{id}/fsm → estados + transições
- GET /mcps/{id}/fsm/current → estado atual
- GET /mcps/{id}/fsm/mermaid → diagrama

## Validação
- [ ] Endpoints retornam dados corretos
- [ ] Registry mostra FSM de MCPs do mcp-builder
'
```

### 2.8 Card 4.2 — Blueprint no Registry

```bash
gh issue create \
  --title "[FASE-4] Blueprint exposto no Registry" \
  --label fase-4-fsm \
  --milestone "M3 — Unificação" \
  --body '
## Descrição
Expor blueprint.yaml via API e CLI.

## Endpoints
- GET /mcps/{id}/blueprint → blueprint.yaml parseado

## Validação
- [ ] GET /mcps/{id}/blueprint → retorna blueprint
- [ ] mcpsctl describe mostra blueprint
- [ ] Se não tem blueprint, 404
'
```

### 2.9 Card 5.1 — 5 Hooks de Governança

```bash
gh issue create \
  --title "[FASE-5] 5 hooks de governança no Registry" \
  --label fase-5-governanca,compliance \
  --milestone "M4 — Governança" \
  --body '
## Hooks
- cost-limit (gate)
- rate-limit (gate)
- audit-log (monitor)
- dependency-vulns (advisor)
- prompt-injection-detector (gate)

## Validação
- [ ] Cada hook tem versão Python e TS
- [ ] POST /mcps/{id}/hooks/run?hook=rate-limit → executa
- [ ] POST /mcps/{id}/hooks/run?hook=cost-limit → bloqueia se excedido
- [ ] 5+ testes por hook
- [ ] Documentação de cada hook
'
```

### 2.10 Card 5.2 — Workflow de Automação

```bash
gh issue create \
  --title "[FASE-5] Workflow de automação do Kanban" \
  --label fase-5-governanca \
  --milestone "M4 — Governança" \
  --body '
## Descrição
Workflow que auto-gerencia o Kanban baseado em eventos.

## Validação
- [ ] Issue aberta → Backlog
- [ ] Issue com label → Doing
- [ ] PR aberto → Review
- [ ] PR merged → Done
' && cd /data/data/com.termux/files/usr/tmp/tmp.8O9M8AvDVk/mcps-as-objects
```

---

## ═══════════════════════════════════════════════════════════════════
## 3. CRIAR WORKFLOWS DE AUTOMAÇÃO
## ═══════════════════════════════════════════════════════════════════

### 3.1 project-automation.yml

```bash
cat > .github/workflows/project-automation.yml << 'YAML'
name: Project Automation
on:
  issues:
    types: [opened, labeled, unlabeled, closed]
  pull_request:
    types: [opened, closed]

jobs:
  automate:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/github-script@v7
        with:
          script: |
            const { data: projects } = await github.rest.projects.listForRepo({
              owner: context.repo.owner,
              repo: context.repo.repo,
            });
            const project = projects.find(p => p.name === 'Integração mcp-builder ↔ mcps-as-objects');
            if (!project) return;
            
            // Mapear colunas por nome
            const { data: columns } = await github.rest.projects.listColumns({
              project_id: project.id,
            });
            const colByName = {};
            columns.forEach(c => { colByName[c.name] = c.id; });
            
            if (context.payload.issue && context.eventName === 'issues') {
              const issueId = context.payload.issue.id;
              const labels = context.payload.issue.labels.map(l => l.name);
              
              if (context.payload.action === 'opened') {
                // Issue aberta → Backlog
                await github.rest.projects.createCard({
                  column_id: colByName['📋 Backlog'],
                  content_id: issueId,
                  content_type: 'Issue',
                });
              } else if (context.payload.action === 'labeled') {
                // Label de fase → Doing
                const faseLabels = ['fase-1-adapter', 'fase-2-templates', 'fase-3-hooks', 'fase-4-fsm', 'fase-5-governanca'];
                if (labels.some(l => faseLabels.includes(l))) {
                  // Move de Backlog para Doing
                  const { data: cards } = await github.rest.projects.listCards({
                    column_id: colByName['📋 Backlog'],
                  });
                  const card = cards.find(c => c.content_id === issueId);
                  if (card) {
                    await github.rest.projects.moveCard({
                      card_id: card.id,
                      position: 'bottom',
                      column_id: colByName['🏗️ Doing'],
                    });
                  }
                }
              } else if (context.payload.action === 'closed') {
                // Issue fechada → Done
                const { data: cardsAll } = await github.rest.projects.listCards({
                  project_id: project.id,
                });
                const card = cardsAll.find(c => c.content_id === issueId);
                if (card && card.column_id !== colByName['📦 Done']) {
                  await github.rest.projects.moveCard({
                    card_id: card.id,
                    position: 'bottom',
                    column_id: colByName['📦 Done'],
                  });
                }
              }
            }
            
            if (context.payload.pull_request && context.eventName === 'pull_request') {
              const prId = context.payload.pull_request.id;
              if (context.payload.action === 'opened') {
                // PR aberto → Review
                // Encontra o card da issue relacionada e move para Review
                // (implementação depende de link entre PR e Issue)
              } else if (context.payload.action === 'closed' && context.payload.pull_request.merged) {
                // PR merged → Done
              }
            }
YAML
```

### 3.2 card-validate.yml

```bash
cat > .github/workflows/card-validate.yml << 'YAML'
name: Card Validate
on:
  project_card:
    types: [moved]

jobs:
  validate:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install deps
        run: pip install -r requirements.txt -q
      - name: Verify all MCPs
        run: python3 scripts/verify-mcp.py --all
      - name: Run adapter tests
        run: python3 -m pytest registry/tests/test_adapter.py -v
YAML
```

---

## ═══════════════════════════════════════════════════════════════════
## 4. IMPLEMENTAÇÃO (por card)
## ═══════════════════════════════════════════════════════════════════

### 4.1 Card 1.1 — adapter.ingest()

**Arquivo:** `registry/src/adapter.py`

```python
"""
adapter.py — Bridge entre mcp-builder (blueprint.yaml) e mcps-as-objects (mcp.json).

Zero hardcoded: tudo lido de blueprint.yaml + schemas.
Agnóstico: funciona com Python, TS, Go, Rust — qualquer SDK/pattern.
Gerenciado: registra no DB, lockfile, verify.
"""

import json
import yaml
from pathlib import Path
from typing import Optional
from . import db, crud, catalog, validator, constructor, verifier


def ingest(
    project_path: str,
    platforms: Optional[list] = None,
    overwrite: bool = False
) -> dict:
    """
    Ingere um projeto gerado pelo mcp-builder no ecossistema mcps-as-objects.

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
    proj = Path(project_path)
    
    # 1. Ler blueprint.yaml ou mcp.json
    blueprint_path = proj / "blueprint.yaml"
    manifest_path = proj / "mcp.json"
    
    if blueprint_path.exists():
        blueprint = yaml.safe_load(blueprint_path.read_text())
        mcp_id = _blueprint_to_id(blueprint)
    elif manifest_path.exists():
        mcp_id = json.loads(manifest_path.read_text())["id"]
        blueprint = {}
    else:
        raise FileNotFoundError(
            f"Nem blueprint.yaml nem mcp.json encontrado em {project_path}"
        )
    
    # 2. Validar contra schema
    if manifest_path.exists():
        valido, erros = validator.validate_manifest_file(str(manifest_path))
        if not valido:
            return {"ok": False, "error": f"Manifesto inválido: {erros}"}
    
    # 3. Verify-mcp
    try:
        ok, msg = verifier.verify_new_mcp(mcp_id)
        if not ok:
            return {"ok": False, "error": f"Verify falhou: {msg}"}
    except Exception as e:
        return {"ok": False, "error": f"Verify exception: {e}"}
    
    # 4. Lockfile
    mhash = catalog.manifest_hash(mcp_id)
    man = catalog.read_manifest(mcp_id)
    if man and mhash:
        catalog.update_lock(mcp_id, man["version"], mhash)
    
    # 5. Registrar no DB
    conn = db.get_conn()
    crud.register_mcp(conn, mcp_id)
    
    return {
        "ok": True,
        "mcp_id": mcp_id,
        "manifest_hash": mhash,
        "action": "ingested",
        "from_blueprint": blueprint_path.exists()
    }
```

### 4.2 Testes — `registry/tests/test_adapter.py`

```python
"""Testes do adapter — 15 testes parametrizados, zero hardcoded."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from adapter import ingest, info, sync

SDKS = ["python", "typescript", "go", "rust"]
PATTERNS = ["stateless", "event", "factory"]

@pytest.mark.parametrize("sdk", SDKS)
@pytest.mark.parametrize("pattern", PATTERNS)
def test_ingest_sdk_pattern(sdk, pattern, tmp_path):
    """Ingest funciona com qualquer SDK + pattern."""
    # Cria blueprint.yaml simulado
    blueprint = tmp_path / "blueprint.yaml"
    blueprint.write_text(f"""
name: test-{sdk}-{pattern}
sdk: {sdk}
pattern: {pattern}
tools:
  - name: ping
    description: Responde pong
    inputSchema: {{}}
""")
    result = ingest(str(tmp_path))
    assert result["ok"]
    assert f"{sdk}" in result["mcp_id"]
```

---

## ═══════════════════════════════════════════════════════════════════
## 5. VERIFICAÇÃO PÓS-EXECUÇÃO
## ═══════════════════════════════════════════════════════════════════

### 5.1 Checklist de Conformidade (projeto todo)

```
□ adapter.ingest() implementado e testado
□ adapter.info() implementado e testado
□ adapter.sync() implementado e testado
□ 15 testes do adapter passando
□ 12 templates mcp.json.hbs criados
□ 1 template server.py.hbs criado
□ Hook post-scaffold funcionando
□ FSM exposto no Registry
□ Blueprint exposto no Registry
□ 5 hooks de governança implementados
□ Workflow project-automation.yml criado
□ GitHub Project configurado com 10 cards
□ 10 Issues abertas com labels e milestones
□ Zero hardcoded: verificado por lint
□ Tudo versionado em git
□ Branch feat/pi-ecosystem-management com tudo commitado
```

### 5.2 Comandos de Verificação

```bash
# Verificar se adapter funciona
python3 -c "from adapter import ingest, info, sync; print('Adapter OK')"

# Verificar se testes passam
python3 -m pytest registry/tests/test_adapter.py -v

# Verificar se verify-mcp ainda passa
python3 scripts/verify-mcp.py --all

# Verificar se lockfile está atualizado
python3 -c "from catalog import read_lockfile; lock = read_lockfile(); print(f'{len(lock.get(\"entries\",{}))} MCPs no lockfile')"

# Verificar se DB tem registros
python3 -c "from db import get_conn; from crud import list_mcps; conn = get_conn(); print(f'{len(list_mcps(conn))} MCPs no DB')"

# Verificar se GitHub Project existe
gh project list --org camillanapoles

# Verificar se Issues foram criadas
gh issue list --label fase-1-adapter
```

---

## ═══════════════════════════════════════════════════════════════════
## 6. TEMPLATE PARA FUTUROS PROJETOS
## ═══════════════════════════════════════════════════════════════════

Este checklist serve como **template replicável** para qualquer projeto futuro:

```
1. Criar GitHub Project (Kanban)
2. Definir labels (categorias + fases)
3. Definir milestones (entregas)
4. Abrir Issues (cards com checklist)
5. Criar workflows de automação
6. Implementar cada card (CRIAR → TESTAR → VALIDAR → COMMITAR)
7. Mover cards no Kanban (event-driven)
8. Verificar conformidade no final
```

**Basta copiar a seção 1 a 5 e adaptar os nomes.** O padrão é sempre o mesmo:
- Issues com checklists de validação
- CI/CD via GitHub Actions
- Kanban event-driven
- Zero hardcoded
- Tudo gerenciado como objeto

---

> **📌 Commit final:** `git add -A && git commit -m "feat: integração mcp-builder completa" && git push`
