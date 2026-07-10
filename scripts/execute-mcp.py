#!/usr/bin/env python3
"""Executa todas as funções de um MCP e salva output."""
import sys, json, importlib.util
sys.path.insert(0, 'registry/src')
from catalog import read_manifest

mcp_id = sys.argv[1]
man = read_manifest(mcp_id)
if not man:
    print(f'Manifesto {mcp_id} nao encontrado')
    sys.exit(1)

mcp_src = f'mcps/{mcp_id}/src'
if mcp_src not in sys.path:
    sys.path.insert(0, mcp_src)

results = {}
for fn in man.get('functions', []):
    fn_name = fn['name']
    print(f'  Rodando {mcp_id}.{fn_name}...', file=sys.stderr)
    try:
        server_path = f'mcps/{mcp_id}/src/server.py'
        spec = importlib.util.spec_from_file_location(f'mcp_{mcp_id}', server_path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
            func = getattr(mod, fn_name, None)
            if func:
                inp = {}
                inp_schema = fn.get('input_schema', {})
                for req in inp_schema.get('required', []):
                    if req in inp_schema.get('properties', {}):
                        prop = inp_schema['properties'][req]
                        if 'default' in prop:
                            inp[req] = prop['default']
                        elif prop.get('type') == 'string':
                            inp[req] = 'auto'
                        elif prop.get('type') == 'number':
                            inp[req] = 0
                        elif prop.get('type') == 'integer':
                            inp[req] = 0
                        elif prop.get('type') == 'boolean':
                            inp[req] = False
                result = func(**inp)
                results[fn_name] = {'status': 'ok', 'result': result}
            else:
                results[fn_name] = {'status': 'error', 'error': 'Funcao nao encontrada no modulo'}
        else:
            results[fn_name] = {'status': 'error', 'error': 'Falha ao carregar servidor'}
    except Exception as exc:
        results[fn_name] = {'status': 'error', 'error': str(exc)}

print(json.dumps(results, indent=2))
with open(f'{mcp_id}_output.json', 'w') as f:
    json.dump(results, f, indent=2)
