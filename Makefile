ROOT  := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
VENV  := $(ROOT)/.venv
PY    := python3
TOOLS := $(ROOT)/tools

.PHONY: all install clean lint test run-dev run-api run-mcp lock check

all: install lint test

# ── Setup ──────────────────────────────────────────────
install:
	$(PY) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r $(ROOT)/requirements.txt
	@echo "✓ Virtualenv em $(VENV)"

setup: install

# ── Lint & Validação ──────────────────────────────────
check: validate lint test

validate:
	$(TOOLS)/mcpsctl validate --all

lint:
	$(VENV)/bin/flake8 $(ROOT)/registry/src || true
	$(VENV)/bin/pylint --disable=C,R $(ROOT)/registry/src || true

# ── Testes ─────────────────────────────────────────────
test:
	cd $(ROOT) && $(VENV)/bin/pytest -v

# ── Execução ───────────────────────────────────────────
run-api:
	cd $(ROOT) && $(VENV)/bin/uvicorn registry.src.api:app --host 127.0.0.1 --port 8712 --reload

run-mcp:
	cd $(ROOT) && PYTHONPATH=$(ROOT)/registry/src $(VENV)/bin/python -m registry.src.server

run-dev: run-api

# ── Lockfile ──────────────────────────────────────────
lock:
	$(TOOLS)/mcpsctl lock

# ── Criação de MCP ────────────────────────────────────
new:
	@$(TOOLS)/mcpsctl new $(id)

# ── Limpeza ────────────────────────────────────────────
clean:
	rm -rf $(VENV)
	rm -rf __pycache__ */__pycache__ */*/__pycache__
	rm -f $(ROOT)/registry/data/registry.db
	find $(ROOT) -name '*.pyc' -delete
	@echo "✓ Limpo"

# ── Info ───────────────────────────────────────────────
info:
	@echo "mcps-as-objects v0.1.0"
	@echo "  ROOT  : $(ROOT)"
	@echo "  VENV  : $(VENV)"
	@echo "  TOOLS : $(TOOLS)"
	@echo "  MCPs  : $$($(TOOLS)/mcpsctl list 2>/dev/null || echo '(none)')"
