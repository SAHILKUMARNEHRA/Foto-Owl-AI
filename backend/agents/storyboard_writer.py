from __future__ import annotations

import json
from pathlib import Path

from backend.rag.retriever import RagRetriever
from backend.schemas.intent import VideoIntent
from backend.schemas.storyboard import ImageAnalysis, Storyboard, StoryboardScene
from backend.utils.ollama import TextModelClient


class StoryboardWriterAgent:
    def __init__(
        self,
        model_client: TextModelClient,
        retriever: RagRetriever,
        default_scene_duration_seconds: float,
    ) -> None:
        self._model_client = model_client
        self._retriever = retriever
        self._default_scene_duration_seconds = default_scene_duration_seconds

    def write(
        self,
        prompt: str,
        intent: VideoIntent,
        selected_images: list[Path],
        image_analysis: list[ImageAnalysis],
    ) -> Storyboard:
        analysis_lookup = {item.image_path: item for item in image_analysis}
        style_docs = self._retriever.retrieve_styles(
            query=f"{intent.video_style}\n{intent.pacing}\n{intent.animation_style}"
        )
        image_context = [
            {
                "image": str(path),
                "scene": analysis_lookup[path].scene,
                "emotion": analysis_lookup[path].emotion,
                "summary": analysis_lookup[path].llm_summary,
                "relevance_score": analysis_lookup[path].relevance_score,
            }
            for path in selected_images
        ]
        payload = self._model_client.invoke_json(
            system_prompt=(
                "You are a storyboard writer for a Remotion image montage. "
                "Return valid JSON with keys: title, creative_rationale, scenes. "
                "Each scene must include image, caption, transition, animation, reason."
            ),
            user_prompt=(
                f"User prompt:\n{prompt}\n\n"
                f"Intent:\n{intent.model_dump_json(indent=2)}\n\n"
                f"Style references:\n{json.dumps(style_docs, indent=2)}\n\n"
                f"Selected image analysis:\n{json.dumps(image_context, indent=2)}\n\n"
                "Use every selected image exactly once and maintain a coherent narrative flow."
            ),
        )
        scenes: list[StoryboardScene] = []
        current_start = 0.0
        raw_scenes = payload.get("scenes", [])
        for index, raw_scene in enumerate(raw_scenes):
            image_path = Path(raw_scene["image"])
            duration = float(raw_scene.get("duration", self._default_scene_duration_seconds))
            scenes.append(
                StoryboardScene(
                    scene_index=index,
                    start_time=current_start,
                    duration=duration,
                    caption=str(raw_scene["caption"]),
                    transition=str(raw_scene["transition"]),
                    image=image_path,
                    animation=str(raw_scene["animation"]),
                    reason=str(raw_scene["reason"]),
                )
            )
            current_start += duration

        return Storyboard(
            title=str(payload.get("title", "FotoOwl Story")),
            total_duration=current_start,
            scenes=scenes,
            creative_rationale=str(payload.get("creative_rationale", "")),
        )
