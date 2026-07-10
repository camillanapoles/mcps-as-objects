# {{ MCP_NAME }}

{{ MCP_DESCRIPTION }}

## Estrutura

```
mcps/{{ MCP_ID }}/
├── mcp.json          # Manifesto (contrato do MCP)
├── src/
│   └── server.py     # Servidor FastMCP
├── tests/
│   └── test_smoke.py # Testes de fumaça
└── README.md         # Esta documentação
```

## Funções

| Função | Descrição |
|--------|-----------|
| `exemplo` | {{ MCP_EXEMPLO_DESCRIPTION }} |

## Uso

```bash
# Rodar localmente
cd {{ MCP_ID }}
python src/server.py
```

## Publicação

1. Valide: `tools/mcpsctl validate {{ MCP_ID }}`
2. Lock: `tools/mcpsctl lock`
3. Commit: o CI valida e publica
