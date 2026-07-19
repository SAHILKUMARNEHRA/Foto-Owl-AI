from __future__ import annotations

import subprocess
from pathlib import Path


class RemotionRenderer:
    def __init__(self, frontend_dir: Path, codec: str = "h264", crf: int = 28) -> None:
        self._frontend_dir = frontend_dir
        self._codec = codec
        self._crf = crf

    def render(self, output_path: Path) -> str:
        completed = subprocess.run(
            [
                "npx",
                "remotion",
                "render",
                "src/index.ts",
                "FotoOwlGenerated",
                str(output_path),
                "--config",
                "remotion.config.ts",
                "--codec",
                self._codec,
                "--crf",
                str(self._crf),
            ],
            cwd=self._frontend_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "Remotion render failed.\n"
                f"stdout:\n{completed.stdout}\n\nstderr:\n{completed.stderr}"
            )
        return completed.stdout + ("\n" + completed.stderr if completed.stderr else "")
