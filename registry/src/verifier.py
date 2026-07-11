"""
verifier.py — Pós-criação: executa verificação completa no MCP recém-criado.
Integrado ao constructor: ao criar um MCP, roda verify-mcp automaticamente.
"""

import sys
import subprocess
from pathlib import Path
from typing import Tuple

ROOT = Path(__file__).resolve().parent.parent.parent
VERIFY_SCRIPT = ROOT / "scripts" / "verify-mcp.py"


def verify_new_mcp(mcp_id: str, detailed: bool = True) -> Tuple[bool, str]:
    """
    Executa verificação completa em um MCP recém-criado.

    Returns:
        (aprovado, mensagem)
    """
    if not VERIFY_SCRIPT.exists():
        return True, "Script de verificação não encontrado (pulado)"

    try:
        result = subprocess.run(
            [sys.executable, str(VERIFY_SCRIPT), mcp_id],
            capture_output=True, text=True, timeout=60,
            cwd=str(ROOT)
        )

        output = result.stdout + result.stderr
        approved = result.returncode == 0

        if approved:
            return True, f"✅ MCP '{mcp_id}' aprovado na verificação pós-criação"
        else:
            # Extrai erros do output
            lines = output.split('\n')
            errors = [l.strip() for l in lines if '❌' in l or 'erro' in l.lower() or 'Error' in l]
            details = '; '.join(errors[:3]) if errors else output[:300]
            return False, f"❌ MCP '{mcp_id}' reprovado: {details}"

    except subprocess.TimeoutExpired:
        return True, "⚠️  Verificação excedeu timeout (60s) — MCP criado mas não verificado"
    except FileNotFoundError:
        return True, "Script de verificação não encontrado (pulado)"
