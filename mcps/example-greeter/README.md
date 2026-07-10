# Example Greeter

MCP de exemplo que demonstra o padrão **mcps-as-objects** completo.

## Funções

| Função | Descrição |
|--------|-----------|
| `greet` | Gera saudação personalizada em pt/en/es |
| `sum` | Soma dois números |

## Executar localmente

```bash
cd mcps/example-greeter
pip install mcp
python src/server.py
```

## Verificar manifesto

```bash
tools/mcpsctl validate example-greeter
```

## Pipeline

```
greet:  → { greeting, lang, timestamp }
sum:    → { result, operation }
```
