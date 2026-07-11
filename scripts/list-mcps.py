#!/usr/bin/env python3
"""List MCPs and output ids+hashes as GITHUB_OUTPUT.
Uso: list-mcps.py [mcp_id_filter]
Se mcp_id_filter for fornecido, retorna apenas aquele.
"""
import sys, json
sys.path.insert(0, 'registry/src')
from catalog import list_mcp_ids, read_manifest

filter_id = sys.argv[1] if len(sys.argv) > 1 else ''
if filter_id:
    ids = [filter_id]
else:
    ids = list_mcp_ids()

print(f'ids={json.dumps(ids)}')
hashes = {}
for mid in ids:
    man = read_manifest(mid)
    if man:
        hashes[mid] = man.get('version', '0.0.0')
print(f'hashes={json.dumps(hashes)}')
