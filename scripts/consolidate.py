#!/usr/bin/env python3
"""Consolidate all MCP outputs into _results.json."""
import json, os

all_results = {}
for dirpath, dirnames, filenames in os.walk('.'):
    for fn in filenames:
        if fn.endswith('_output.json'):
            fpath = os.path.join(dirpath, fn)
            mcp_id = fn.replace('_output.json', '')
            try:
                all_results[mcp_id] = json.load(open(fpath))
            except Exception as exc:
                all_results[mcp_id] = {'error': str(exc)}

with open('_results.json', 'w') as out:
    json.dump(all_results, out, indent=2)

print(f'Consolidado: {len(all_results)} MCP(s)')
for mid, res in all_results.items():
    status = 'OK' if isinstance(res, dict) and all(
        v.get('status') == 'ok' for v in res.values()
    ) else 'FAIL'
    print(f'  {mid}: {status}')
