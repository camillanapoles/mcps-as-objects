# Patterns — Convenções Determinísticas

Este documento define as **regras rígidas** de nomenclatura, estrutura e composição que todo MCP deve seguir. Desvios são detectados na validação.

## 1. Nomenclatura

| Entidade | Padrão | Exemplo |
|----------|--------|---------|
| **ID do MCP** | `^[a-z][a-z0-9-]*[a-z0-9]$` (kebab-case) | `meu-servico`, `data-processor-v2` |
| **Nome** | Title Case | `Meu Serviço`, `Data Processor V2` |
| **Versão** | Semver | `0.1.0`, `1.2.3-beta.1` |
| **Função** | `^[a-z][a-z0-9_]*$` (snake_case) | `gerar_relatorio`, `process_file` |
| **Arquivos servidor** | `src/server.py` (ou .js, .ts, .go) | fixo |
| **Testes** | `tests/test_*.py` | `test_smoke.py` |
| **Diretório MCP** | `mcps/<id>/` | `mcps/meu-servico/` |

## 2. Estrutura de Diretórios (imutável)

```
mcps/<mcp-id>/
├── mcp.json          # OBRIGATÓRIO — manifesto
├── src/
│   └── server.py     # OBRIGATÓRIO — entrypoint MCP
├── tests/
│   └── test_*.py     # RECOMENDADO — pelo menos test_smoke.py
└── README.md         # RECOMENDADO
```

Nada além disso. Sem subdiretórios extras. Sem arquivos soltos.

## 3. O Manifesto (`mcp.json`)

Deve ser válido contra `schemas/mcp-manifest.schema.json`.

```jsonc
{
  "id": "meu-mcp",                // kebab-case
  "name": "Meu MCP",              // Title Case
  "version": "0.1.0",             // semver
  "description": "...",           // obrigatório
  "entry": "src/server.py",       // sempre src/ e o nome do arquivo
  "runtime": {
    "language": "python",         // python | node | go
    "image": "ubuntu-22.04",
    "estimated_duration_sec": 60,
    "dependencies": { "python": "requirements.txt" }
  },
  "functions": [
    {
      "name": "minha_funcao",     // snake_case
      "description": "…",
      "input_schema": { … },      // JSON Schema
      "output_schema": { … }      // JSON Schema
    }
  ]
}
```

## 4. Funções

- Cada função no `mcp.json` **deve** ter uma correspondente `@mcp.tool()` no `src/server.py`.
- O nome da ferramenta MCP **deve** ser idêntico ao `function.name` no manifesto.
- `input_schema` **deve** ter `type: object` e `properties`.
- Campos em `required` no schema **devem** estar em `properties`.

## 5. Runtime

- O MCP server deve ser executável via `python src/server.py` ou comando equivalente.
- O server **deve** expor um transporte __stdio__ (padrão MCP) — não obrigatório para execução em workflow, mas necessário para integração com pi-coding.
- Dependências: `requirements.txt` para Python, `package.json` para Node, `go.mod` para Go.

## 6. Pipeline (Composição)

```jsonc
"pipeline": {
  "consumes": ["mcp-id.function_name"],  // de quem depende
  "produces": ["mcp-id.function_name"]   // o que oferece
}
```

- `consumes` vazio = MCP raiz (pode ser executado independentemente)
- `produces` vazio = MCP terminal (apenas consome)

## 7. Lockfile (`mcps-lock.json`)

- Mantido via `tools/mcpsctl lock`
- Hash SHA-256 de cada `mcp.json`
- Usado como **chave de cache determinística**
- Versionado: `entries.<id>.manifest_hash`

## 8. Cache Key

```
mcp-snapshot-v1-{sha256(mcps-lock.json)}-{sha256(uname -a)[:12]}
```

## 9. Validação

Dois momentos:
- **CI** (PR): `mcp-validate.yml` — bloqueia manifesto inválido
- **Runtime** (antes de executar): `validate_mcp()` — verificação extra
