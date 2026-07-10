"""
Python Termux Builder — Core Logic (sem dependência do MCP SDK).
Lógica de detecção, análise e build de wheels para Termux/Android.

Pode ser testada sem o pacote `mcp` (útil em ambientes com restrições).
"""

import json
import os
import re
import subprocess
import hashlib
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timezone

CACHE_DIR = Path(__file__).resolve().parent.parent / "wheels"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

GH_REPO = "camillanapoles/android-wheel-factory"
GH_WORKFLOW = "android-wheel.yml"

# ── Catálogos de compatibilidade ──────────────────────────────────

NEEDS_EXTERNAL_BUILD = {
    "rpds-py": {"type": "rust-ext",   "reason": "rpds-py precisa de Rust para compilar. Sem rustc no Termux padrão."},
    "cryptography": {"type": "c-ext", "reason": "cryptography precisa de OpenSSL headers e compilador C."},
    "numpy":  {"type": "c-ext",       "reason": "numpy compila em Termux via pkg, mas versão PyPI falha sem BLAS."},
    "pandas": {"type": "c-ext",       "reason": "pandas depende de numpy compilado."},
    "psutil": {"type": "c-ext",       "reason": "psutil precisa de headers do kernel."},
    "lxml":   {"type": "c-ext",       "reason": "lxml precisa de libxml2/libxslt headers."},
    "ujson":  {"type": "c-ext",       "reason": "ujson compila C, pode falhar sem toolchain."},
    "orjson": {"type": "rust-ext",    "reason": "orjson precisa de Rust para compilar."},
    "matplotlib": {"type": "c-ext",   "reason": "matplotlib tem várias deps C (freetype, png)."},
    "scipy":  {"type": "c-ext",       "reason": "scipy precisa de BLAS/LAPACK compilados."},
    "bcrypt": {"type": "c-ext",       "reason": "bcrypt compila C, precisa de toolchain."},
    "cffi":   {"type": "c-ext",       "reason": "cffi compila C extensions — precisa de gcc."},
    "greenlet": {"type": "c-ext",     "reason": "greenlet compila C extension."},
    "gevent": {"type": "c-ext",       "reason": "gevent compila C e depende de greenlet."},
    "uvloop": {"type": "c-ext",       "reason": "uvloop precisa de libuv e compilador C."},
    "pydantic-core": {"type": "rust-ext", "reason": "pydantic-core usa Pydantic (Rust) para validação — precisa de rustc."},
}

PURE_PYTHON = {
    "click", "typer", "rich", "starlette", "pydantic",
    "uvicorn", "httpx", "requests", "urllib3",
    "certifi", "charset-normalizer", "idna", "six", "python-dotenv",
    "pyyaml", "tomli", "tomllib", "typing-extensions", "typing-inspection",
    "anyio", "sniffio", "h11", "wsproto", "websockets",
    "jsonschema", "attrs", "pyrsistent",
    "fastjsonschema", "jsonpointer", "jsonpatch",
    "mcp", "pip", "setuptools", "wheel",
    "colorama", "tqdm", "tabulate", "jinja2", "markupsafe",
    "asgiref", "multidict", "yarl", "frozenlist",
    "python-dateutil", "pytz", "tzdata",
    "fastapi", "httptools", "watchfiles",
    "orjson", "ciso8601",
}


def _get_package_info_from_pypi(package_name: str) -> Optional[dict]:
    """Consulta PyPI para obter info do pacote."""
    import urllib.request
    import urllib.error
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "mcps-as-objects/0.1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError, OSError):
        return None


def _has_extension_wheels(info: dict) -> tuple:
    """Verifica se pacote tem wheels com extensões nativas (C/Rust)."""
    if not info:
        return False, "unknown"
    has_pure = any(
        u["packagetype"] == "bdist_wheel" and "none-any.whl" in u["filename"]
        for u in info.get("urls", [])
    )
    has_abi3 = any(
        u["packagetype"] == "bdist_wheel" and "abi3" in u["filename"]
        for u in info.get("urls", [])
    )
    has_platform = any(
        u["packagetype"] == "bdist_wheel" and "manylinux" in u["filename"]
        for u in info.get("urls", [])
    )
    if has_pure and not has_abi3 and not has_platform:
        return False, "pure-python"
    elif has_abi3 or has_platform:
        return True, "c-ext"
    elif any(u["packagetype"] == "sdist" for u in info.get("urls", [])) and not has_pure:
        return True, "needs-compile"
    else:
        return False, "unknown"


# ── Funções públicas (testáveis) ──────────────────────────────────


def check_package(package_name: str, python_version: str = "3.12") -> dict:
    """
    Verifica se um pacote Python pode ser instalado em Termux.
    """
    pkg = package_name.lower().strip()

    if pkg in PURE_PYTHON:
        return {
            "package": pkg, "compatible": True,
            "reason": "Pacote 100% Python — funciona no Termux sem toolchain.",
            "type": "pure-python", "needs_external_build": False,
            "alternatives": [], "python_version": python_version
        }

    if pkg in NEEDS_EXTERNAL_BUILD:
        meta = NEEDS_EXTERNAL_BUILD[pkg]
        return {
            "package": pkg, "compatible": False,
            "reason": meta["reason"],
            "type": meta["type"], "needs_external_build": True,
            "alternatives": [f"build_wheel('{pkg}')"],
            "python_version": python_version
        }

    # Fallback: consulta PyPI
    info = _get_package_info_from_pypi(pkg)
    if info:
        has_ext, ext_type = _has_extension_wheels(info)
        if not has_ext:
            return {
                "package": pkg, "compatible": True,
                "reason": "Apenas wheels pure-Python disponíveis no PyPI.",
                "type": "pure-python", "needs_external_build": False,
                "alternatives": [], "python_version": python_version
            }
        summary = info.get("info", {}).get("summary", "")[:200]
        return {
            "package": pkg, "compatible": False,
            "reason": f"Extensões nativas detectadas ({ext_type}). {summary}",
            "type": ext_type, "needs_external_build": True,
            "alternatives": [
                f"Verificar via pkg: pkg install python-{pkg}",
                f"build_wheel('{pkg}', python_version='{python_version}')"
            ],
            "python_version": python_version
        }

    return {
        "package": pkg, "compatible": True,
        "reason": "Não foi possível determinar. Assumindo pure-Python.",
        "type": "unknown", "needs_external_build": False,
        "alternatives": [f"Consultar pypi.org/project/{pkg}"],
        "python_version": python_version
    }


def build_wheel(package_name: str, package_version: str = "",
                python_version: str = "3.12") -> dict:
    """
    Dispara build externo de wheel aarch64 via GitHub Actions (gh CLI).
    """
    pkg = package_name.lower().strip()
    try:
        cmd = [
            "gh", "workflow", "run", GH_WORKFLOW,
            "--repo", GH_REPO,
            "-f", f"python_version={python_version}",
            "-f", f"package_name={pkg}",
        ]
        if package_version:
            cmd.extend(["-f", f"package_version={package_version}"])
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            run_url = result.stdout.strip()
            run_id = run_url.split("/")[-1] if run_url else ""
            return {
                "success": True, "action": "build_triggered",
                "package": pkg, "python_version": python_version,
                "run_id": run_id, "run_url": run_url,
                "status": "queued", "error": ""
            }
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return {
        "success": False, "action": "manual_instructions",
        "package": pkg, "python_version": python_version,
        "run_id": "", "run_url": "", "status": "unknown",
        "error": (
            "gh CLI não disponível. Para build manual:\n"
            f"  gh workflow run {GH_WORKFLOW} --repo {GH_REPO} -f python_version={python_version} -f package_name={pkg}\n"
            f"  gh run download <run-id> --repo={GH_REPO} -n wheels --dir {CACHE_DIR}"
        )
    }


def list_cached_wheels(package_name: str = "") -> dict:
    """Lista wheels Android disponíveis no cache local."""
    wheels = []
    for f in CACHE_DIR.glob("**/*.whl"):
        if package_name and package_name.lower() not in f.name.lower():
            continue
        parts = f.name.split("-")
        wheels.append({
            "package": parts[0] if parts else "",
            "version": parts[1] if len(parts) > 1 else "",
            "python_version": "3.12",
            "arch": "aarch64",
            "path": str(f),
            "size": f.stat().st_size
        })
    return {"wheels": sorted(wheels, key=lambda w: w["package"]), "total": len(wheels)}


def check_requirements(requirements_text: str) -> dict:
    """Analisa requirements.txt e reporta compatibilidade Termux."""
    lines = requirements_text.strip().split("\n")
    compatible, needs_build, unknown = [], [], []

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        pkg_name = re.split(r"[<>=!~]", line)[0].strip().lower()
        if not pkg_name:
            continue
        if pkg_name in PURE_PYTHON:
            compatible.append(pkg_name)
        elif pkg_name in NEEDS_EXTERNAL_BUILD:
            needs_build.append(pkg_name)
        else:
            info = _get_package_info_from_pypi(pkg_name)
            if info:
                has_ext, _ = _has_extension_wheels(info)
                (needs_build if has_ext else compatible).append(pkg_name)
            else:
                unknown.append(pkg_name)

    total = len(compatible) + len(needs_build) + len(unknown)

    if needs_build:
        summary = (f"{len(compatible)} compatíveis, {len(needs_build)} precisam de build. "
                   f"Use build_wheel() para cada um.")
    elif unknown:
        summary = f"{len(compatible)} compatíveis, {len(unknown)} não identificados."
    else:
        summary = f"Todos os {total} pacotes são compatíveis com Termux. ✓"

    return {
        "total_packages": total,
        "compatible": sorted(compatible),
        "needs_build": sorted(needs_build),
        "unknown": sorted(unknown),
        "summary": summary
    }
