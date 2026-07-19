from __future__ import annotations

from pydantic import BaseModel, Field


class VideoIntent(BaseModel):
    video_style: str = Field(description="Overall visual style for the edit.")
    caption_tone: str = Field(description="Tone to use for captions and text overlays.")
    pacing: str = Field(description="Narrative pacing such as slow, medium, or fast.")
    transition_style: str = Field(description="Preferred transitions between scenes.")
    text_overlay: str = Field(description="How text should appear in the video.")
    animation_style: str = Field(description="Motion style for image treatment.")
    music_mood: str = Field(description="Desired mood for background music.")
    color_palette: str = Field(description="Color direction or grade for the final video.")
