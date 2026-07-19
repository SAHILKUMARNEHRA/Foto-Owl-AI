from __future__ import annotations

import argparse
import sys
from pathlib import Path

from backend.config import get_settings
from backend.pipeline import run_pipeline
from backend.utils.files import ensure_directory
from backend.utils.logging import configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the FotoOwl image-to-video pipeline.")
    parser.add_argument("--input-dir", required=True, help="Directory containing event images.")
    parser.add_argument("--prompt", required=True, help="Creative brief for the video.")
    return parser


def run() -> int:
    args = build_parser().parse_args()
    settings = get_settings()
    configure_logging(settings.log_level)
    input_dir = Path(args.input_dir).resolve()
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    ensure_directory(settings.outputs_dir)
    final_state = run_pipeline(settings=settings, input_dir=input_dir, prompt=args.prompt)
    return 0 if final_state.render_status == "completed" else 1


if __name__ == "__main__":
    sys.exit(run())
