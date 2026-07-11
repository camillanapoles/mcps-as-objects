"""
Platform Detector — reconhece a máquina atual e filtra MCPs por compatibilidade.

Taxonomia:
  linux/amd64        → GitHub Actions runner, Ubuntu amd64
  linux/arm64        → ARM64 Linux (ex: Raspberry Pi)
  android/termux     → Termux no Android (aarch64)
  darwin/amd64       → macOS Intel
  darwin/arm64       → macOS Apple Silicon
  *                  → Qualquer plataforma (MCP universal)
"""

import os
import sys
import subprocess as _subprocess
from pathlib import Path
from typing import List, Optional
import sys as _sys
# Importa o platform da stdlib, não o nosso módulo
_sys_path_backup = list(_sys.path)
_sys.path = [p for p in _sys.path if 'registry/src' not in p]
import platform as _sys_platform
_sys.path = _sys_path_backup


def detect_platform() -> str:
    """
    Detecta a plataforma atual e retorna uma string normalizada.
    Exemplos: 'linux/amd64', 'android/termux', 'darwin/arm64'.
    """
    system = _sys_platform.system().lower() if hasattr(_sys_platform, 'system') else "unknown"
    machine = _sys_platform.machine().lower() if hasattr(_sys_platform, 'machine') else "unknown"

    # Android via Termux
    _is_termux = (
        os.environ.get("TERMUX_VERSION") is not None
        or os.environ.get("PREFIX", "").startswith("/data/data/com.termux")
        or os.path.exists("/data/data/com.termux/files/usr/bin/termux-info")
    )
    if _is_termux:
        return "android/termux"

    if system == "linux":
        return f"linux/{machine}"

    if system == "darwin":
        return f"darwin/{machine}"

    return f"{system}/{machine}"


def detect_platforms() -> List[str]:
    """Retorna lista de plataformas aplicáveis (herança)."""
    current = detect_platform()
    platforms = [current]

    # android/termux também conta como linux/arm64 para compatibilidade
    if current == "android/termux":
        machine = _sys_platform.machine().lower()
        platforms.append(f"linux/{machine}")

    if "*" not in platforms:
        platforms.append("*")

    return platforms


def mcp_is_compatible(manifest: dict,
                      target_platforms: Optional[List[str]] = None) -> tuple:
    """
    Verifica se um MCP é compatível com a plataforma atual (ou fornecida).

    Returns:
        (compativel, razao)
    """
    if target_platforms is None:
        target_platforms = detect_platforms()

    mcp_platforms = manifest.get("platforms", ["*"])

    if "*" in mcp_platforms:
        return True, "MCP universal (plataformas: *)"

    for mp in mcp_platforms:
        if mp in target_platforms:
            return True, f"MCP compatível com {mp}"

    return False, (
        f"MCP incompatível. Plataformas do MCP: {mcp_platforms}. "
        f"Plataforma atual: {target_platforms[0]}. "
        f"Este MCP só funciona em: {', '.join(mcp_platforms)}"
    )


def filter_mcps_by_platform(manifests: dict) -> dict:
    """
    Filtra um dicionário {mcp_id: manifest} para incluir apenas
    MCPs compatíveis com a plataforma atual.
    """
    current = detect_platform()
    result = {}
    for mid, man in manifests.items():
        ok, reason = mcp_is_compatible(man)
        result[mid] = {
            "manifest": man,
            "compatible": ok,
            "reason": reason,
            "platform_current": current
        }
    return result


def platform_label(platform_str: str) -> str:
    """Retorna label amigável para uma plataforma."""
    labels = {
        "linux/amd64": "🐧 Linux amd64",
        "linux/arm64": "🐧 Linux ARM64",
        "android/termux": "📱 Android Termux",
        "darwin/amd64": "🍎 macOS Intel",
        "darwin/arm64": "🍎 macOS Apple Silicon",
    }
    return labels.get(platform_str, f"❓ {platform_str}")


if __name__ == "__main__":
    print(f"Plataforma detectada: {detect_platform()}")
    print(f"Plataformas aplicáveis: {detect_platforms()}")
    print(f"Label: {platform_label(detect_platform())}")
