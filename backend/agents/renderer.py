from __future__ import annotations

from pathlib import Path

from backend.renderer.render import RemotionRenderer


class RendererAgent:
    def __init__(self, renderer: RemotionRenderer, frontend_dir: Path) -> None:
        self._renderer = renderer
        self._frontend_dir = frontend_dir

    def render(self, output_path: Path, render_log_path: Path) -> str:
        result = self._renderer.render(output_path=output_path)
        render_log_path.write_text(result, encoding="utf-8")
        return result
