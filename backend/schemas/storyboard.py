from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class ImageAnalysis(BaseModel):
    image_path: Path
    people: list[str] = Field(default_factory=list)
    objects: list[str] = Field(default_factory=list)
    scene: str
    emotion: str
    quality: str
    blur_score: float
    brightness: float
    composition: str
    relevance_score: float
    llm_summary: str


class StoryboardScene(BaseModel):
    scene_index: int
    start_time: float
    duration: float
    caption: str
    transition: str
    image: Path
    animation: str
    reason: str


class Storyboard(BaseModel):
    title: str
    total_duration: float
    scenes: list[StoryboardScene] = Field(default_factory=list)
    creative_rationale: str
