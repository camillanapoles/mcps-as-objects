# Meu Novo Serviço

Serviço de teste do pipeline pre-staging

## Estrutura

```
mcps/meu-novo-servico/
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
| `exemplo` | Função exemplo de Meu Novo Serviço |

## Uso

```bash
# Rodar localmente
cd meu-novo-servico
python src/server.py
```

## Publicação

1. Valide: `tools/mcpsctl validate meu-novo-servico`
2. Lock: `tools/mcpsctl lock`
3. Commit: o CI valida e publica
