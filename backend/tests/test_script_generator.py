from pathlib import Path

from backend.agents.script_generator import ScriptGeneratorAgent
from backend.schemas.intent import VideoIntent
from backend.schemas.storyboard import Storyboard, StoryboardScene
from backend.tests.fakes import FakeRetriever, FakeTextClient


def test_script_generator_writes_valid_script_files(tmp_path: Path) -> None:
    frontend_dir = tmp_path / "frontend"
    generated_dir = frontend_dir / "src" / "generated"
    generated_dir.mkdir(parents=True)
    (frontend_dir / "public").mkdir()

    image_path = tmp_path / "scene.jpg"
    image_path.write_bytes(b"image-bytes")

    storyboard = Storyboard(
        title="Event Recap",
        total_duration=3.0,
        creative_rationale="Strong opening beat.",
        scenes=[
            StoryboardScene(
                scene_index=0,
                start_time=0.0,
                duration=3.0,
                caption="Opening moment",
                transition="fade",
                image=image_path,
                animation="slow push-in",
                reason="Lead with the hero frame",
            )
        ],
    )
    intent = VideoIntent(
        video_style="cinematic",
        caption_tone="warm",
        pacing="medium",
        transition_style="fade",
        text_overlay="minimal",
        animation_style="slow push-in",
        music_mood="hopeful",
        color_palette="gold and charcoal",
    )

    agent = ScriptGeneratorAgent(
        model_client=FakeTextClient(
            json_responses=[
                {
                    "title_treatment": "Launch Night",
                    "caption_font_scale": 1.0,
                    "overlay_opacity": 0.3,
                    "motion_bias": "subtle drift",
                    "transition_frames": 12,
                    "gradient_strength": 0.7,
                }
            ]
        ),
        retriever=FakeRetriever(docs=[{"text": "Use Sequence with AbsoluteFill."}]),
        frontend_dir=frontend_dir,
        generated_dir=generated_dir,
        fps=30,
    )

    script = agent.generate(intent=intent, storyboard=storyboard, outputs_dir=tmp_path / "outputs")

    assert "AbsoluteFill" in script
    assert (tmp_path / "outputs" / "generated_script.tsx").exists()
    assert (generated_dir / "GeneratedVideo.tsx").exists()
    assert (frontend_dir / "public" / "generated_assets" / "scene_00.jpg").exists()
