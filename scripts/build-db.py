#!/usr/bin/env python3
"""Build SQLite DB with all MCPs registered."""
import sys
sys.path.insert(0, 'registry/src')
from db import get_conn
from crud import scan_and_register_all
conn = get_conn()
scan_and_register_all(conn)
print('DB snapshot ready')
