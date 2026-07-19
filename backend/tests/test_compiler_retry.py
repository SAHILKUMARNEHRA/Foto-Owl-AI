from pathlib import Path
from types import SimpleNamespace

from backend.config import Settings
from backend.agents.compiler_fixer import CompilerFixerAgent
from backend.graph.edges import route_after_compile
from backend.graph.nodes import PipelineNodes
from backend.schemas.compiler_error import CompileResult
from backend.schemas.pipeline_state import PipelineState
from backend.tests.fakes import FakeCompiler, compile_error


class FakeFixer:
    def fix(self, script: str, compile_result: CompileResult, script_path: Path, output_copy_path: Path) -> str:
        fixed = script.replace("BROKEN", "FIXED")
        script_path.parent.mkdir(parents=True, exist_ok=True)
        output_copy_path.parent.mkdir(parents=True, exist_ok=True)
        script_path.write_text(fixed, encoding="utf-8")
        output_copy_path.write_text(fixed, encoding="utf-8")
        return fixed


def test_compiler_retry_flow_patches_and_recovers(tmp_path: Path) -> None:
    settings = Settings(
        outputs_dir=tmp_path / "outputs",
        remotion_generated_dir=tmp_path / "frontend" / "src" / "generated",
        frontend_dir=tmp_path / "frontend",
    )
    nodes = PipelineNodes(
        container=SimpleNamespace(
            compiler=FakeCompiler(
                [
                    compile_error("Expected '}'"),
                    CompileResult(success=True, stdout="ok", stderr="", exit_code=0, issues=[]),
                ]
            ),
            compiler_fixer=FakeFixer(),
            renderer=None,
        ),
        settings=settings,
    )
    state = PipelineState(input_dir=tmp_path, prompt="prompt", script="const BROKEN = true;")

    compiler_update = nodes.compiler(state)
    failed_state = state.model_copy(update=compiler_update)
    assert route_after_compile(failed_state) == "fix"

    fixed_update = nodes.compiler_fixer(failed_state)
    retried_state = failed_state.model_copy(update=fixed_update)
    assert retried_state.retry_count == 1
    assert "FIXED" in retried_state.script

    success_update = nodes.compiler(retried_state)
    success_state = retried_state.model_copy(update=success_update)
    assert route_after_compile(success_state) == "render"


def test_compiler_fixer_strips_markdown_fences() -> None:
    fixed_script = CompilerFixerAgent._sanitize_script(
        """```tsx
import React from "react";

export default function GeneratedVideo() {
  return null;
}
```"""
    )

    assert fixed_script.startswith('import React from "react";')
    assert "```" not in fixed_script
