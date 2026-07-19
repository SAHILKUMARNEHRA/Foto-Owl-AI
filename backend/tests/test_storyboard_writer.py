from pathlib import Path

from backend.agents.storyboard_writer import StoryboardWriterAgent
from backend.schemas.intent import VideoIntent
from backend.schemas.storyboard import ImageAnalysis
from backend.tests.fakes import FakeRetriever, FakeTextClient


def test_storyboard_writer_builds_timed_scenes(tmp_path: Path) -> None:
    image_path = tmp_path / "hero.jpg"
    image_path.write_text("x", encoding="utf-8")
    agent = StoryboardWriterAgent(
        model_client=FakeTextClient(
            json_responses=[
                {
                    "title": "Launch Night",
                    "creative_rationale": "Builds from anticipation to celebration.",
                    "scenes": [
                        {
                            "image": str(image_path),
                            "caption": "The room fills with anticipation.",
                            "transition": "fade",
                            "animation": "slow push-in",
                            "reason": "Strong opening image",
                            "duration": 3.5,
                        }
                    ],
                }
            ]
        ),
        retriever=FakeRetriever(styles=[{"text": "Prefer emotional openings."}]),
        default_scene_duration_seconds=3.0,
    )

    intent = VideoIntent(
        video_style="cinematic",
        caption_tone="warm",
        pacing="medium",
        transition_style="fade",
        text_overlay="minimal",
        animation_style="slow push-in",
        music_mood="hopeful",
        color_palette="golden",
    )
    analysis = [
        ImageAnalysis(
            image_path=image_path,
            people=["speaker"],
            objects=["stage"],
            scene="keynote",
            emotion="excited",
            quality="high",
            blur_score=100.0,
            brightness=140.0,
            composition="balanced",
            relevance_score=9.0,
            llm_summary="Hero shot",
        )
    ]

    storyboard = agent.write("Tell a launch-night story", intent, [image_path], analysis)

    assert storyboard.total_duration == 3.5
    assert storyboard.scenes[0].caption.startswith("The room")
