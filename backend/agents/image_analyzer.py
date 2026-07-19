from __future__ import annotations

import logging
from pathlib import Path

from backend.schemas.storyboard import ImageAnalysis
from backend.utils.image_metrics import compute_blur_score, compute_brightness
from backend.utils.ollama import VisionModelClient

LOGGER = logging.getLogger(__name__)


class ImageAnalyzerAgent:
    def __init__(self, vision_client: VisionModelClient, max_selected_images: int) -> None:
        self._vision_client = vision_client
        self._max_selected_images = max_selected_images

    def analyze(self, image_paths: list[Path], prompt: str) -> tuple[list[ImageAnalysis], list[Path]]:
        analyses: list[ImageAnalysis] = []
        for image_path in image_paths:
            brightness = compute_brightness(image_path)
            blur_score = compute_blur_score(image_path)
            system_prompt = (
                "You analyze event photography for a narrative image-to-video edit. "
                "Return JSON with keys: people, objects, scene, emotion, quality, "
                "composition, relevance_score, llm_summary. The relevance_score must be 0-10."
            )
            user_prompt = (
                f"User prompt: {prompt}\n"
                "Assess how useful this image is for the requested video and describe the scene clearly."
            )
            payload = self._vision_client.analyze_image(
                image_path=image_path,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            analysis = ImageAnalysis(
                image_path=image_path,
                people=self._normalize_string_list(payload.get("people", [])),
                objects=self._normalize_string_list(payload.get("objects", [])),
                scene=str(payload.get("scene", "unknown scene")),
                emotion=str(payload.get("emotion", "neutral")),
                quality=str(payload.get("quality", "unknown")),
                blur_score=blur_score,
                brightness=brightness,
                composition=str(payload.get("composition", "unknown")),
                relevance_score=float(payload.get("relevance_score", 0.0)),
                llm_summary=str(payload.get("llm_summary", "")),
            )
            analyses.append(analysis)

        scored = sorted(analyses, key=self._combined_score, reverse=True)
        selected = [item.image_path for item in scored[: self._max_selected_images]]
        LOGGER.info("Selected %s images from %s analyzed inputs.", len(selected), len(analyses))
        return analyses, selected

    @staticmethod
    def _combined_score(analysis: ImageAnalysis) -> float:
        sharpness = min(analysis.blur_score / 1500.0, 3.0)
        normalized_brightness = 1.0 - min(abs(analysis.brightness - 128.0) / 128.0, 1.0)
        quality_bonus = 0.5 if analysis.quality.lower() in {"high", "excellent"} else 0.0
        return (analysis.relevance_score * 1.4) + sharpness + normalized_brightness + quality_bonus

    @staticmethod
    def _normalize_string_list(value: object) -> list[str]:
        if isinstance(value, str):
            items = [item.strip() for item in value.split(",")]
            return [item for item in items if item and item.lower() != "none"]
        if isinstance(value, list):
            normalized = [str(item).strip() for item in value]
            return [item for item in normalized if item and item.lower() != "none"]
        return []
