"""
Validador determinístico de manifestos MCP.
Usa JSON Schema como fonte única de verdade.
"""

import json
import fastjsonschema
from pathlib import Path
from typing import List, Tuple, Optional, Union

SCHEMAS_DIR = Path(__file__).resolve().parent.parent.parent / "schemas"

# Cache de schema compilados
_validators: dict = {}


def _compile(name: str):
    """Compila e cacheia um schema JSON."""
    if name not in _validators:
        path = SCHEMAS_DIR / name
        if not path.exists():
            raise FileNotFoundError(f"Schema não encontrado: {path}")
        schema = json.loads(path.read_text())
        _validators[name] = fastjsonschema.compile(schema)
    return _validators[name]


def validate_manifest(manifest: dict) -> Tuple[bool, List[str]]:
    """
    Valida um dict de manifesto contra o schema.
    Retorna (valido, lista_de_erros).
    """
    errors = []
    try:
        fn = _compile("mcp-manifest.schema.json")
        fn(manifest)
    except fastjsonschema.JsonSchemaException as exc:
        errors.append(f"manifesto: {exc.message}")
        return False, errors
    except Exception as exc:
        errors.append(f"manifesto: {exc}")
        return False, errors

    # Valida funções individualmente
    for idx, fn in enumerate(manifest.get("functions", [])):
        fn_errors = _validate_function_io(fn)
        if fn_errors:
            errors.append(f"functions[{idx}].{fn.get('name','?')}: {fn_errors}")

    return len(errors) == 0, errors


def _validate_function_io(fn: dict) -> List[str]:
    """Valida schemas de input/output de uma função."""
    errors = []
    inp = fn.get("input_schema", {})
    outp = fn.get("output_schema", {})

    # Verifica se input tem type=object e properties
    if inp:
        if inp.get("type") != "object":
            errors.append("input_schema.type deve ser 'object'")
        if "properties" not in inp:
            errors.append("input_schema.properties é obrigatório")

    if outp:
        if not isinstance(outp.get("type"), str):
            errors.append("output_schema.type é obrigatório")

    return errors


def validate_lockfile(lockfile: dict) -> Tuple[bool, List[str]]:
    """Valida o mcps-lock.json contra o schema."""
    errors = []
    try:
        fn = _compile("lockfile.schema.json")
        fn(lockfile)
    except fastjsonschema.JsonSchemaException as exc:
        errors.append(f"lockfile: {exc.message}")
        return False, errors
    except Exception as exc:
        errors.append(f"lockfile: {exc}")
        return False, errors
    return True, errors


def validate_manifest_file(path: Union[str, Path]) -> Tuple[bool, List[str]]:
    """Carrega e valida um arquivo de manifesto."""
    if isinstance(path, str):
        path = Path(path)
    if not path.exists():
        return False, [f"Arquivo não encontrado: {path}"]
    try:
        manifest = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return False, [f"JSON inválido: {exc}"]
    return validate_manifest(manifest)
