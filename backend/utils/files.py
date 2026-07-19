from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, payload: Any) -> None:
    ensure_directory(path.parent)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    ensure_directory(path.parent)
    path.write_text(content, encoding="utf-8")


def list_image_files(directory: Path) -> list[Path]:
    extensions = {".jpg", ".jpeg", ".png", ".webp"}
    return sorted(path for path in directory.iterdir() if path.suffix.lower() in extensions and path.is_file())
