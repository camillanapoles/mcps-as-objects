#!/usr/bin/env python3
"""Compute cache snapshot key for deterministic caching."""
import hashlib, os, subprocess

lock = open('mcps-lock.json','rb').read() if os.path.exists('mcps-lock.json') else b'{}'
h = hashlib.sha256(lock).hexdigest()
u = subprocess.run(['uname','-a'], capture_output=True, text=True).stdout.encode('utf-8')
rh = hashlib.sha256(u).hexdigest()[:12]
print(f'mcp-snapshot-v1-{h}-{rh}')
