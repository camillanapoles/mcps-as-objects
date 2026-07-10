# Authoring — Como Criar um Novo MCP

Este guia mostra como criar um novo MCP seguindo o padrão determinístico.

## 1. Via CLI (recomendado)

```bash
tools/mcpsctl new meu-mcp --name "Meu MCP" --desc "Processa dados de entrada"
```

Isso cria:

```
mcps/meu-mcp/
├── mcp.json
├── src/
│   └── server.py
├── tests/
│   └── test_smoke.py
└── README.md
```

## 2. Editar o Manifesto

Edite `mcps/meu-mcp/mcp.json`:

```jsonc
{
  "id": "meu-mcp",
  "name": "Meu MCP",
  "version": "0.1.0",
  "description": "Processa dados de entrada e gera relatório.",
  "entry": "src/server.py",
  "runtime": {
    "language": "python",
    "image": "ubuntu-22.04",
    "estimated_duration_sec": 60,
    "dependencies": { "python": "requirements.txt" }
  },
  "functions": [
    {
      "name": "processar",
      "description": "Processa os dados e retorna relatório.",
      "input_schema": {
        "type": "object",
        "properties": {
          "dados": { "type": "string", "description": "Dados de entrada" },
          "modo": { "type": "string", "enum": ["rapido", "completo"], "default": "rapido" }
        },
        "required": ["dados"]
      },
      "output_schema": {
        "type": "object",
        "properties": {
          "relatorio": { "type": "string" },
          "modo_usado": { "type": "string" },
          "timestamp": { "type": "string" }
        },
        "required": ["relatorio", "modo_usado", "timestamp"]
      }
    }
  ],
  "permissions": [],
  "pipeline": {
    "consumes": [],
    "produces": ["meu-mcp.processar"]
  },
  "tags": ["processamento"]
}
```

## 3. Implementar o Servidor

Edite `mcps/meu-mcp/src/server.py`:

```python
from datetime import datetime, timezone
from typing import Optional
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("meu-mcp", "Processa dados de entrada e gera relatório.")

@mcp.tool()
def processar(dados: str, modo: Optional[str] = "rapido") -> dict:
    """
    Processa os dados e retorna relatório.

    Args:
        dados: Dados de entrada.
        modo: Modo de processamento (rapido, completo).
    """
    # Sua lógica aqui
    relatorio = f"Processado ({modo}): {len(dados)} caracteres"
    return {
        "relatorio": relatorio,
        "modo_usado": modo or "rapido",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

if __name__ == "__main__":
    mcp.run()
```

## 4. Validar

```bash
tools/mcpsctl validate meu-mcp
# ✓ meu-mcp
```

## 5. Testar

```bash
cd mcps/meu-mcp
pip install mcp
python src/server.py    # Isso inicia o MCP em modo stdio
```

Ou via API:

```bash
make run-api
curl -X POST http://127.0.0.1:8712/mcps/meu-mcp/run \
  -H "Content-Type: application/json" \
  -d '{"function_name": "processar", "input_payload": {"dados": "teste", "modo": "rapido"}}'
```

## 6. Atualizar Lockfile

```bash
tools/mcpsctl lock
```

## 7. Commit

```bash
git add mcps/meu-mcp/
git commit -m "feat: novo MCP meu-mcp"
git push
```

O CI (`mcp-validate.yml`) valida automaticamente.
