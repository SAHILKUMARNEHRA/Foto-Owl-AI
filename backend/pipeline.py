from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from backend.config import Settings
from backend.dependencies import build_container
from backend.graph.workflow import build_workflow
from backend.schemas.pipeline_state import PipelineState, TimestampLog
from backend.utils.files import ensure_directory, write_json


def run_pipeline(settings: Settings, input_dir: Path, prompt: str) -> PipelineState:
    ensure_directory(settings.outputs_dir)
    ensure_directory(settings.remotion_generated_dir)
    ensure_directory(settings.frontend_dir / "public" / "generated_assets")

    container = build_container(settings)
    workflow = build_workflow(container=container, settings=settings)
    initial_state = PipelineState(
        input_dir=input_dir.resolve(),
        prompt=prompt,
        timestamps=[TimestampLog(stage="started", timestamp=datetime.now(UTC))],
    )

    try:
        result = workflow.invoke(initial_state)
        final_state = PipelineState.model_validate(result)
    except Exception as exc:  # pragma: no cover - defensive production path
        final_state = initial_state.model_copy(
            update={
                "render_status": "failed",
                "failure_reason": str(exc),
                "pipeline_logs": [*initial_state.pipeline_logs, "exception"],
                "timestamps": [
                    *initial_state.timestamps,
                    TimestampLog(stage="exception", timestamp=datetime.now(UTC)),
                ],
            }
        )

    write_json(settings.outputs_dir / "pipeline_state.json", json.loads(final_state.model_dump_json()))
    return final_state
