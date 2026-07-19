from __future__ import annotations

from backend.schemas.storyboard import Storyboard
from backend.utils.ollama import TextModelClient


def judge_narrative_coherence(
    model_client: TextModelClient,
    prompt: str,
    storyboard: Storyboard,
) -> dict[str, object]:
    return model_client.invoke_json(
        system_prompt=(
            "You are a strict video narrative judge. "
            "Return JSON with keys: score, verdict, reasoning. "
            "Score must be 1-10 and reasoning must mention flow, pacing, and caption consistency."
        ),
        user_prompt=(
            f"User prompt:\n{prompt}\n\n"
            f"Storyboard:\n{storyboard.model_dump_json(indent=2)}"
        ),
    )
