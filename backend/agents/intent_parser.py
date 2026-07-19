from __future__ import annotations

import logging

from pydantic import ValidationError

from backend.schemas.intent import VideoIntent
from backend.utils.ollama import TextModelClient

LOGGER = logging.getLogger(__name__)


class IntentParserAgent:
    def __init__(self, model_client: TextModelClient) -> None:
        self._model_client = model_client

    def parse(self, prompt: str) -> VideoIntent:
        system_prompt = (
            "You convert user prompts for an image-to-video edit into structured JSON. "
            "Return only valid JSON with keys: video_style, caption_tone, pacing, "
            "transition_style, text_overlay, animation_style, music_mood, color_palette."
        )
        user_prompt = f"Prompt:\n{prompt}\n\nRespond with concise production-ready values."
        payload = self._model_client.invoke_json(system_prompt=system_prompt, user_prompt=user_prompt)
        try:
            intent = VideoIntent.model_validate(payload)
        except ValidationError as exc:
            LOGGER.exception("Intent parsing validation failed.")
            raise ValueError(f"Invalid intent response: {payload}") from exc
        return intent
