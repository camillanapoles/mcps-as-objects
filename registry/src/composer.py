"""
Pipeline Composer — orquestra execução em pipeline de MCPs.
Cada MCP declara `pipeline.consumes` e `pipeline.produces`,
o que permite compor grafo DAG de execução.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class PipelineNode:
    mcp_id: str
    function_name: str
    depends_on: List[str] = field(default_factory=list)
    input: Optional[dict] = None
    output: Optional[dict] = None


@dataclass
class PipelineGraph:
    """Grafo DAG de dependências entre MCPs."""
    nodes: Dict[str, PipelineNode] = field(default_factory=dict)

    def add(self, node: PipelineNode):
        key = f"{node.mcp_id}.{node.function_name}"
        self.nodes[key] = node

    def execution_order(self) -> List[PipelineNode]:
        """
        Retorna nós em ordem topológica (dependências primeiro).
        Simples: depende do campo `depends_on` em formato `mcp_id.func`.
        """
        visited = set()
        order = []

        def dfs(key: str):
            if key in visited:
                return
            visited.add(key)
            node = self.nodes[key]
            for dep in node.depends_on:
                if dep in self.nodes:
                    dfs(dep)
            order.append(node)

        for key in self.nodes:
            dfs(key)

        return order


def build_graph_from_manifests(manifests: Dict[str, dict]) -> PipelineGraph:
    """
    Constrói PipelineGraph a partir de manifestos.
    Lê campo `pipeline` de cada MCP.
    """
    graph = PipelineGraph()
    for mcp_id, man in manifests.items():
        pipeline = man.get("pipeline", {})
        produces = pipeline.get("produces", [])
        consumes = pipeline.get("consumes", [])

        # Cada função do MCP vira um node
        for fn in man.get("functions", []):
            fn_name = fn["name"]
            key = f"{mcp_id}.{fn_name}"
            node = PipelineNode(
                mcp_id=mcp_id,
                function_name=fn_name,
                depends_on=consumes
            )
            graph.add(node)
    return graph
