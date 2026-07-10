# Processador de Texto

Analisa e processa textos — exemplo de MCP replicável

## Estrutura

```
mcps/processador-texto/
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
| `exemplo` | Função exemplo de Processador de Texto |

## Uso

```bash
# Rodar localmente
cd processador-texto
python src/server.py
```

## Publicação

1. Valide: `tools/mcpsctl validate processador-texto`
2. Lock: `tools/mcpsctl lock`
3. Commit: o CI valida e publica
