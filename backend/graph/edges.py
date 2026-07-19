from __future__ import annotations

from backend.schemas.pipeline_state import PipelineState


def route_after_compile(state: PipelineState | dict) -> str:
    pipeline_state = PipelineState.model_validate(state)
    latest = pipeline_state.compile_errors[-1]
    if latest.success:
        return "render"
    if pipeline_state.retry_count >= 3:
        return "failed"
    return "fix"
