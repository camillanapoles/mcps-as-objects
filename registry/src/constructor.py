"""
Constructor — cria novos MCPs a partir do template determinístico.
É o que torna o sistema replicável: dado um spec, materializa
o MCP inteiro com estrutura, manifesto, servidor, testes e docs.
"""

import json
import shutil
from pathlib import Path
from typing import Optional

TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "mcps" / "_template"
MCPS_DIR = TEMPLATE_DIR.parent


def create_mcp(
    mcp_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    version: str = "0.1.0",
    overwrite: bool = False,
) -> Path:
    """
    Cria um novo MCP a partir do template.

    Args:
        mcp_id: ID kebab-case (ex: 'meu-mcp')
        name: Nome amigável (opcional, default: nome capitalizado)
        description: Descrição (opcional)
        version: Versão semver
        overwrite: Se True, sobrescreve diretório existente

    Returns:
        Path para o diretório do novo MCP.

    Raises:
        FileExistsError: se mcp_id já existe e overwrite=False.
    """
    import re
    if not re.match(r'^[a-z][a-z0-9-]*[a-z0-9]$', mcp_id):
        raise ValueError(
            f"ID inválido: '{mcp_id}'. Use kebab-case: letras minúsculas, "
            "números e hífens. Ex: 'meu-servico'"
        )

    dest = MCPS_DIR / mcp_id
    if dest.exists() and not overwrite:
        raise FileExistsError(
            f"MCP '{mcp_id}' já existe em {dest}. Use overwrite=True para sobrescrever."
        )

    # Copia template
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(TEMPLATE_DIR, dest)

    # Preenche placeholders no manifesto
    manifest_path = dest / "mcp.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["id"] = mcp_id
    manifest["name"] = name or mcp_id.replace("-", " ").title()
    manifest["description"] = description or f"MCP {mcp_id}"
    manifest["version"] = version
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    # Preenche placeholders no server.py
    server_path = dest / "src" / "server.py"
    server_content = server_path.read_text()
    replacements = {
        "{{ MCP_NAME }}": manifest["name"],
        "{{ MCP_DESCRIPTION }}": manifest["description"],
        "{{ MCP_VERSION }}": version,
        "{{ MCP_EXEMPLO_DESCRIPTION }}": f"Função exemplo de {manifest['name']}",
    }
    for old, new in replacements.items():
        server_content = server_content.replace(old, new)
    server_path.write_text(server_content)

    # Preenche README
    readme = dest / "README.md"
    readme_content = readme.read_text()
    for old, new in {
        "{{ MCP_ID }}": mcp_id,
        "{{ MCP_NAME }}": manifest["name"],
        "{{ MCP_DESCRIPTION }}": manifest["description"],
        "{{ MCP_EXEMPLO_DESCRIPTION }}": f"Função exemplo de {manifest['name']}",
    }.items():
        readme_content = readme_content.replace(old, new)
    readme.write_text(readme_content)

    return dest
