from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from backend.schemas.compiler_error import CompileResult
from backend.schemas.intent import VideoIntent
from backend.schemas.storyboard import ImageAnalysis, Storyboard


class TimestampLog(BaseModel):
    stage: str
    timestamp: datetime


class PipelineState(BaseModel):
    input_dir: Path
    prompt: str
    images: list[Path] = Field(default_factory=list)
    selected_images: list[Path] = Field(default_factory=list)
    image_analysis: list[ImageAnalysis] = Field(default_factory=list)
    video_intent: VideoIntent | None = None
    storyboard: Storyboard | None = None
    script: str = ""
    compile_errors: list[CompileResult] = Field(default_factory=list)
    retry_count: int = 0
    render_status: str = "pending"
    final_video_path: Path | None = None
    pipeline_logs: list[str] = Field(default_factory=list)
    timestamps: list[TimestampLog] = Field(default_factory=list)
    failure_reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
