#!/usr/bin/env python3
"""List MCPs and output ids+hashes as GITHUB_OUTPUT."""
import sys, json
sys.path.insert(0, 'registry/src')
from catalog import list_mcp_ids, read_manifest
ids = list_mcp_ids()
print(f'ids={json.dumps(ids)}')
hashes = {}
for mid in ids:
    man = read_manifest(mid)
    if man:
        hashes[mid] = man.get('version', '0.0.0')
print(f'hashes={json.dumps(hashes)}')
