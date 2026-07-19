from pathlib import Path

from backend.schemas.storyboard import Storyboard, StoryboardScene
from backend.tests.fakes import FakeTextClient
from backend.utils.evaluators import judge_narrative_coherence


def test_llm_as_judge_narrative_coherence_returns_score() -> None:
    storyboard = Storyboard(
        title="Launch Night",
        total_duration=6.0,
        creative_rationale="Moves from anticipation to applause.",
        scenes=[
            StoryboardScene(
                scene_index=0,
                start_time=0.0,
                duration=3.0,
                caption="Guests gather before the keynote.",
                transition="fade",
                image=Path("/tmp/scene-1.jpg"),
                animation="slow push-in",
                reason="Establishes the room",
            ),
            StoryboardScene(
                scene_index=1,
                start_time=3.0,
                duration=3.0,
                caption="Applause lands on the final reveal.",
                transition="fade",
                image=Path("/tmp/scene-2.jpg"),
                animation="slow push-in",
                reason="Pays off the build-up",
            ),
        ],
    )
    client = FakeTextClient(
        json_responses=[
            {
                "score": 9,
                "verdict": "coherent",
                "reasoning": "The flow is clear, pacing is balanced, and the captions stay consistent.",
            }
        ]
    )

    result = judge_narrative_coherence(client, "Create an uplifting event recap", storyboard)

    assert result["score"] == 9
    assert result["verdict"] == "coherent"
