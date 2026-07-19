from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from backend.config import Settings
from backend.dependencies import Container
from backend.schemas.pipeline_state import PipelineState, TimestampLog
from backend.utils.files import ensure_directory, list_image_files, write_json, write_text


def _as_state(value: PipelineState | dict) -> PipelineState:
    return PipelineState.model_validate(value)


def _log(state: PipelineState, message: str) -> tuple[list[str], list[TimestampLog]]:
    logs = [*state.pipeline_logs, message]
    timestamps = [*state.timestamps, TimestampLog(stage=message, timestamp=datetime.now(UTC))]
    return logs, timestamps


class PipelineNodes:
    def __init__(self, container: Container, settings: Settings) -> None:
        self._container = container
        self._settings = settings

    def intent_parser(self, state: PipelineState | dict) -> dict:
        pipeline_state = _as_state(state)
        logs, timestamps = _log(pipeline_state, "intent_parser")
        intent = self._container.intent_parser.parse(pipeline_state.prompt)
        write_json(self._settings.outputs_dir / "video_intent.json", intent.model_dump(mode="json"))
        return {"video_intent": intent, "pipeline_logs": logs, "timestamps": timestamps}

    def image_analyzer(self, state: PipelineState | dict) -> dict:
        pipeline_state = _as_state(state)
        images = list_image_files(pipeline_state.input_dir)
        analyses, selected = self._container.image_analyzer.analyze(images, pipeline_state.prompt)
        logs, timestamps = _log(pipeline_state, "image_analyzer")
        write_json(
            self._settings.outputs_dir / "analysis.json",
            [item.model_dump(mode="json") for item in analyses],
        )
        return {
            "images": images,
            "image_analysis": analyses,
            "selected_images": selected,
            "pipeline_logs": logs,
            "timestamps": timestamps,
        }

    def storyboard_writer(self, state: PipelineState | dict) -> dict:
        pipeline_state = _as_state(state)
        storyboard = self._container.storyboard_writer.write(
            prompt=pipeline_state.prompt,
            intent=pipeline_state.video_intent,
            selected_images=pipeline_state.selected_images,
            image_analysis=pipeline_state.image_analysis,
        )
        logs, timestamps = _log(pipeline_state, "storyboard_writer")
        write_json(self._settings.outputs_dir / "storyboard.json", storyboard.model_dump(mode="json"))
        return {"storyboard": storyboard, "pipeline_logs": logs, "timestamps": timestamps}

    def script_generator(self, state: PipelineState | dict) -> dict:
        pipeline_state = _as_state(state)
        ensure_directory(self._settings.outputs_dir)
        script = self._container.script_generator.generate(
            intent=pipeline_state.video_intent,
            storyboard=pipeline_state.storyboard,
            outputs_dir=self._settings.outputs_dir,
        )
        logs, timestamps = _log(pipeline_state, "script_generator")
        return {"script": script, "pipeline_logs": logs, "timestamps": timestamps}

    def compiler(self, state: PipelineState | dict) -> dict:
        pipeline_state = _as_state(state)
        compile_result = self._container.compiler.compile()
        logs, timestamps = _log(pipeline_state, "compiler")
        compile_results = [*pipeline_state.compile_errors, compile_result]
        write_text(
            self._settings.outputs_dir / "compile_log.txt",
            compile_result.stdout + ("\n" + compile_result.stderr if compile_result.stderr else ""),
        )
        return {"compile_errors": compile_results, "pipeline_logs": logs, "timestamps": timestamps}

    def compiler_fixer(self, state: PipelineState | dict) -> dict:
        pipeline_state = _as_state(state)
        fixed_script = self._container.compiler_fixer.fix(
            script=pipeline_state.script,
            compile_result=pipeline_state.compile_errors[-1],
            script_path=self._settings.remotion_generated_dir / "GeneratedVideo.tsx",
            output_copy_path=self._settings.outputs_dir / "generated_script.tsx",
        )
        logs, timestamps = _log(pipeline_state, "compiler_fixer")
        return {
            "script": fixed_script,
            "retry_count": pipeline_state.retry_count + 1,
            "pipeline_logs": logs,
            "timestamps": timestamps,
        }

    def renderer(self, state: PipelineState | dict) -> dict:
        pipeline_state = _as_state(state)
        final_video_path = self._settings.outputs_dir / "final_video.mp4"
        self._container.renderer.render(
            output_path=final_video_path,
            render_log_path=self._settings.outputs_dir / "render_log.txt",
        )
        logs, timestamps = _log(pipeline_state, "renderer")
        return {
            "render_status": "completed",
            "final_video_path": final_video_path,
            "pipeline_logs": logs,
            "timestamps": timestamps,
        }

    def failure(self, state: PipelineState | dict) -> dict:
        pipeline_state = _as_state(state)
        logs, timestamps = _log(pipeline_state, "failed")
        return {
            "render_status": "failed",
            "failure_reason": "Compilation failed after maximum retries.",
            "pipeline_logs": logs,
            "timestamps": timestamps,
        }
