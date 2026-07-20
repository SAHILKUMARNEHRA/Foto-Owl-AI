from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from backend.config import Settings
from backend.dependencies import build_container
from backend.graph.workflow import build_workflow
from backend.schemas.pipeline_state import PipelineState, TimestampLog
from backend.utils.files import ensure_directory, write_json


def _is_quota_error(message: str) -> bool:
    lowered = message.lower()
    return any(
        marker in lowered
        for marker in (
            "429",
            "quota",
            "resource_exhausted",
            "rate limit",
            "rate-limit",
        )
    )


def run_pipeline(settings: Settings, input_dir: Path, prompt: str) -> PipelineState:
    ensure_directory(settings.outputs_dir)
    ensure_directory(settings.remotion_generated_dir)
    ensure_directory(settings.frontend_dir / "public" / "generated_assets")

    initial_state = PipelineState(
        input_dir=input_dir.resolve(),
        prompt=prompt,
        timestamps=[TimestampLog(stage="started", timestamp=datetime.now(UTC))],
    )

    try:
        container = build_container(settings)
        workflow = build_workflow(container=container, settings=settings)
        result = workflow.invoke(initial_state)
        final_state = PipelineState.model_validate(result)
    except Exception as exc:  # pragma: no cover - defensive production path
        error_message = str(exc)
        if settings.fallback_to_offline_on_quota and settings.llm_provider.lower() == "gemini" and _is_quota_error(error_message):
            fallback_settings = settings.model_copy(update={"llm_provider": "offline"})
            fallback_container = build_container(fallback_settings)
            fallback_workflow = build_workflow(container=fallback_container, settings=fallback_settings)
            fallback_state = initial_state.model_copy(
                update={
                    "pipeline_logs": [
                        *initial_state.pipeline_logs,
                        "gemini_quota_exhausted",
                        "offline_fallback_started",
                    ],
                    "metadata": {
                        **initial_state.metadata,
                        "fallback_reason": error_message,
                        "fallback_provider": "offline",
                    },
                }
            )
            result = fallback_workflow.invoke(fallback_state)
            fallback_result = PipelineState.model_validate(result)
            final_state = fallback_result.model_copy(
                update={
                    "pipeline_logs": [
                        *fallback_result.pipeline_logs,
                        "offline_fallback_completed",
                    ],
                    "metadata": {
                        **fallback_result.metadata,
                        "fallback_reason": error_message,
                        "fallback_provider": "offline",
                    },
                }
            )
        else:
            final_state = initial_state.model_copy(
                update={
                    "render_status": "failed",
                    "failure_reason": error_message,
                    "pipeline_logs": [*initial_state.pipeline_logs, "exception"],
                    "timestamps": [
                        *initial_state.timestamps,
                        TimestampLog(stage="exception", timestamp=datetime.now(UTC)),
                    ],
                }
            )

    write_json(settings.outputs_dir / "pipeline_state.json", json.loads(final_state.model_dump_json()))
    return final_state
