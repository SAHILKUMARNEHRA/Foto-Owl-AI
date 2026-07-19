from pathlib import Path

from backend.agents.renderer import RendererAgent
from backend.tests.fakes import FakeRenderer


def test_renderer_agent_writes_render_log_and_output(tmp_path: Path) -> None:
    output_path = tmp_path / "final.mp4"
    log_path = tmp_path / "render_log.txt"
    renderer = FakeRenderer()
    agent = RendererAgent(renderer=renderer, frontend_dir=tmp_path)

    result = agent.render(output_path=output_path, render_log_path=log_path)

    assert result == "render ok"
    assert output_path.exists()
    assert log_path.read_text(encoding="utf-8") == "render ok"
