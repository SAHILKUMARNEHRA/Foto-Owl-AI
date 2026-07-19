from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from backend.config import Settings
from backend.dependencies import Container
from backend.graph.edges import route_after_compile
from backend.graph.nodes import PipelineNodes
from backend.schemas.pipeline_state import PipelineState


def build_workflow(container: Container, settings: Settings):
    nodes = PipelineNodes(container=container, settings=settings)
    graph = StateGraph(PipelineState)

    graph.add_node("intent_parser", nodes.intent_parser)
    graph.add_node("image_analyzer", nodes.image_analyzer)
    graph.add_node("storyboard_writer", nodes.storyboard_writer)
    graph.add_node("script_generator", nodes.script_generator)
    graph.add_node("compiler", nodes.compiler)
    graph.add_node("compiler_fixer", nodes.compiler_fixer)
    graph.add_node("renderer", nodes.renderer)
    graph.add_node("failed", nodes.failure)

    graph.add_edge(START, "intent_parser")
    graph.add_edge("intent_parser", "image_analyzer")
    graph.add_edge("image_analyzer", "storyboard_writer")
    graph.add_edge("storyboard_writer", "script_generator")
    graph.add_edge("script_generator", "compiler")
    graph.add_conditional_edges(
        "compiler",
        route_after_compile,
        {
            "render": "renderer",
            "fix": "compiler_fixer",
            "failed": "failed",
        },
    )
    graph.add_edge("compiler_fixer", "compiler")
    graph.add_edge("renderer", END)
    graph.add_edge("failed", END)

    return graph.compile()
