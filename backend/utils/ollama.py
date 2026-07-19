from __future__ import annotations

import base64
import json
import mimetypes
import re
import time
from pathlib import Path
from typing import Any, Protocol

import requests


class TextModelClient(Protocol):
    def invoke_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        ...

    def invoke_text(self, system_prompt: str, user_prompt: str) -> str:
        ...


class VisionModelClient(Protocol):
    def analyze_image(self, image_path: Path, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        ...


def _extract_json_payload(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```").strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
    return json.loads(cleaned)


class OfflineTextClient:
    def invoke_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        lowered = f"{system_prompt}\n{user_prompt}".lower()
        if "corrected_script" in lowered:
            return {"corrected_script": self._extract_script(user_prompt)}
        if "style directives" in lowered:
            return self._style_directives(user_prompt)
        if "storyboard writer" in lowered:
            return self._storyboard(user_prompt)
        if "storyboard writer" in lowered:
            return self._storyboard(user_prompt)
        if "video_style" in lowered and "caption_tone" in lowered:
            return self._intent(user_prompt)
        if "narrative" in lowered and "coherence" in lowered:
            return {"score": 8, "reason": "The storyboard has a clear beginning, middle, and ending."}
        return {"text": "offline response"}

    def invoke_text(self, system_prompt: str, user_prompt: str) -> str:
        return json.dumps(self.invoke_json(system_prompt=system_prompt, user_prompt=user_prompt))

    @staticmethod
    def _intent(user_prompt: str) -> dict[str, Any]:
        text = user_prompt.lower()
        is_fast = any(word in text for word in ("upbeat", "fast", "energetic", "birthday"))
        is_corporate = "corporate" in text or "professional" in text
        is_warm = "warm" in text or "wedding" in text or "emotional" in text
        return {
            "video_style": "clean corporate highlights" if is_corporate else "cinematic event reel",
            "caption_tone": "bold and energetic" if is_fast else "minimal and emotional",
            "pacing": "fast" if is_fast else "measured and slow",
            "transition_style": "quick cuts" if is_fast else "smooth fades",
            "text_overlay": "bold captions" if is_fast else "minimal lower-third captions",
            "animation_style": "snappy zooms" if is_fast else "gentle zoom and slow pan",
            "music_mood": "energetic" if is_fast else "warm and reflective",
            "color_palette": "neutral corporate tones" if is_corporate else ("warm golden tones" if is_warm else "natural tones"),
        }

    @staticmethod
    def _storyboard(user_prompt: str) -> dict[str, Any]:
        marker = "Selected image analysis:"
        image_context: list[dict[str, Any]] = []
        if marker in user_prompt:
            raw = user_prompt.split(marker, 1)[1]
            start = raw.find("[")
            if start != -1:
                image_context = json.JSONDecoder().raw_decode(raw[start:])[0]
        captions = [
            "The day opens with quiet anticipation.",
            "Warm smiles gather into a shared story.",
            "Details and faces become lasting memories.",
            "The celebration settles into a graceful finale.",
        ]
        scenes = []
        for index, item in enumerate(image_context):
            scenes.append(
                {
                    "image": item["image"],
                    "duration": 3.0,
                    "caption": captions[index % len(captions)],
                    "transition": "Fade" if index % 2 == 0 else "Cross Dissolve",
                    "animation": "Gentle Zoom In" if index % 2 == 0 else "Slow Pan",
                    "reason": f"Selected for its {item.get('emotion', 'event')} mood and narrative relevance.",
                }
            )
        return {
            "title": "Cinematic Event Memories",
            "creative_rationale": "A warm, emotional sequence that moves from anticipation to celebration and closes with a reflective finish.",
            "scenes": scenes,
        }

    @staticmethod
    def _style_directives(user_prompt: str) -> dict[str, Any]:
        return {
            "title_treatment": "Elegant cinematic title treatment",
            "caption_font_scale": 1.0,
            "overlay_opacity": 0.22,
            "motion_bias": "gentle",
            "transition_frames": 24,
            "gradient_strength": 0.34,
        }

    @staticmethod
    def _extract_script(user_prompt: str) -> str:
        marker = "Current script:"
        if marker not in user_prompt:
            return ""
        return user_prompt.split(marker, 1)[1].strip()


class OfflineVisionClient:
    def analyze_image(self, image_path: Path, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        stem = image_path.stem.replace("_", " ").replace("-", " ").strip()
        number_match = re.search(r"\d+", stem)
        scene_number = number_match.group(0) if number_match else stem or "event"
        return {
            "people": ["event guests"],
            "objects": ["decor", "venue", "celebration details"],
            "scene": f"Event photograph {scene_number}",
            "emotion": "warm and celebratory",
            "quality": "high",
            "composition": "balanced event composition with useful subject framing",
            "relevance_score": 8.0,
            "llm_summary": f"{image_path.name} contributes a polished moment to the event recap.",
        }


class OllamaTextClient:
    def __init__(self, base_url: str, model: str, timeout: int = 120) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    def invoke_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        response_text = self._chat(system_prompt=system_prompt, user_prompt=user_prompt, response_format="json")
        return _extract_json_payload(response_text)

    def invoke_text(self, system_prompt: str, user_prompt: str) -> str:
        return self._chat(system_prompt=system_prompt, user_prompt=user_prompt, response_format=None)

    def _chat(self, system_prompt: str, user_prompt: str, response_format: str | None) -> str:
        payload = {
            "model": self._model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if response_format is not None:
            payload["format"] = response_format
        response = requests.post(
            f"{self._base_url}/api/chat",
            json=payload,
            timeout=self._timeout,
        )
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]


class OllamaVisionClient:
    def __init__(self, base_url: str, model: str, timeout: int = 180) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    def analyze_image(self, image_path: Path, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        image_bytes = image_path.read_bytes()
        payload = {
            "model": self._model,
            "format": "json",
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": user_prompt,
                    "images": [base64.b64encode(image_bytes).decode("utf-8")],
                },
            ],
        }
        response = requests.post(
            f"{self._base_url}/api/chat",
            json=payload,
            timeout=self._timeout,
        )
        response.raise_for_status()
        data = response.json()
        return _extract_json_payload(data["message"]["content"])


class GeminiTextClient:
    def __init__(
        self,
        api_base_url: str,
        api_key: str,
        model: str,
        timeout: int = 120,
        max_retries: int = 3,
    ) -> None:
        self._api_base_url = api_base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._max_retries = max_retries

    def invoke_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        text = self._generate(
            system_prompt=system_prompt,
            user_parts=[{"text": user_prompt}],
            response_mime_type="application/json",
        )
        return _extract_json_payload(text)

    def invoke_text(self, system_prompt: str, user_prompt: str) -> str:
        return self._generate(
            system_prompt=system_prompt,
            user_parts=[{"text": user_prompt}],
            response_mime_type="text/plain",
        )

    def _generate(
        self,
        system_prompt: str,
        user_parts: list[dict[str, Any]],
        response_mime_type: str,
    ) -> str:
        response = None
        for attempt in range(self._max_retries + 1):
            response = requests.post(
                f"{self._api_base_url}/models/{self._model}:generateContent",
                params={"key": self._api_key},
                json={
                    "systemInstruction": {"parts": [{"text": system_prompt}]},
                    "contents": [{"role": "user", "parts": user_parts}],
                    "generationConfig": {"responseMimeType": response_mime_type},
                },
                timeout=self._timeout,
            )
            try:
                response.raise_for_status()
                break
            except requests.HTTPError as exc:
                status_code = exc.response.status_code if exc.response is not None else None
                if status_code in {429, 500, 502, 503, 504} and attempt < self._max_retries:
                    time.sleep(2**attempt)
                    continue
                detail = exc.response.text.strip() if exc.response is not None else str(exc)
                raise RuntimeError(
                    f"Gemini request failed with status {status_code}: {detail}"
                ) from exc

        if response is None:
            raise RuntimeError("Gemini request did not produce a response.")
        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError(f"Gemini returned no candidates: {data}")
        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(str(part.get("text", "")) for part in parts if "text" in part).strip()
        if not text:
            raise ValueError(f"Gemini returned no text parts: {data}")
        return text


class GeminiVisionClient:
    def __init__(self, api_base_url: str, api_key: str, model: str, timeout: int = 180) -> None:
        self._text_client = GeminiTextClient(
            api_base_url=api_base_url,
            api_key=api_key,
            model=model,
            timeout=timeout,
        )

    def analyze_image(self, image_path: Path, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        mime_type = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
        text = self._text_client._generate(
            system_prompt=system_prompt,
            user_parts=[
                {"text": user_prompt},
                {
                    "inlineData": {
                        "mimeType": mime_type,
                        "data": base64.b64encode(image_path.read_bytes()).decode("utf-8"),
                    }
                },
            ],
            response_mime_type="application/json",
        )
        return _extract_json_payload(text)
