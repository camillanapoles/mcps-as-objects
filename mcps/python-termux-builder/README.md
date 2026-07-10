# Python Termux Builder

Gerencia dependências Python no **Termux/Android**.

## Problema

Pacotes Python com extensões nativas (C, Rust, C++) **não compilam** no Termux porque faltam toolchains (`gcc`, `rustc`, `make`, headers do sistema).

Exemplo concreto vivido durante o desenvolvimento deste projeto:

```
pip install jsonschema
  → rpds-py (Rust) falha: "can't find Rust compiler"
  → jsonschema não instala
```

## Solução

Este MCP:

1. **Detecta** automaticamente se um pacote é compatível com Termux
2. **Cataloga** pacotes conhecidos (pure-Python ✅ vs C/Rust ❌)
3. **Dispara build externo** de wheels `aarch64` via GitHub Actions (`android-wheel-factory`)
4. **Cacheia** wheels localmente para reuso

## Ferramentas

| Função | Descrição |
|--------|-----------|
| `check_package(package_name)` | Diagnostica compatibilidade de um pacote |
| `build_wheel(package_name, version, py_version)` | Dispara build de wheel aarch64 |
| `list_cached_wheels(package_name?)` | Lista wheels em cache local |
| `check_requirements(requirements_text)` | Analisa requirements.txt completo |

## Exemplo

```python
# Verificar pacote
result = check_package("rpds-py")
# → { "compatible": false, "type": "rust-ext", "needs_external_build": true }

# Build externo via GitHub Actions
build = build_wheel("rpds-py", python_version="3.12")
# → { "success": true, "run_id": "1234", "status": "queued" }

# Analisar requirements.txt
result = check_requirements("""click
rpds-py
fastapi
cryptography""")
# → { "compatible": ["click", "fastapi"], "needs_build": ["cryptography", "rpds-py"] }
```

## Integração

```bash
# Ver pacote
tools/mcpsctl describe python-termux-builder

# Rodar MCP localmente
cd mcps/python-termux-builder && python src/server.py
```
