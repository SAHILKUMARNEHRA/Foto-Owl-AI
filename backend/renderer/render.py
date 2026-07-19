from __future__ import annotations

import subprocess
from pathlib import Path


class RemotionRenderer:
    def __init__(self, frontend_dir: Path) -> None:
        self._frontend_dir = frontend_dir

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
