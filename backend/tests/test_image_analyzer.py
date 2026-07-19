from pathlib import Path

from PIL import Image

from backend.agents.image_analyzer import ImageAnalyzerAgent
from backend.tests.fakes import FakeVisionClient


def _create_image(path: Path, color: tuple[int, int, int]) -> None:
    Image.new("RGB", (320, 240), color=color).save(path)


def test_image_analyzer_scores_and_selects_best_images(tmp_path: Path) -> None:
    first = tmp_path / "a.jpg"
    second = tmp_path / "b.jpg"
    _create_image(first, (255, 180, 180))
    _create_image(second, (40, 50, 60))

    agent = ImageAnalyzerAgent(
        vision_client=FakeVisionClient(
            [
                {
                    "people": ["speaker"],
                    "objects": ["stage"],
                    "scene": "keynote",
                    "emotion": "excited",
                    "quality": "high",
                    "composition": "centered subject",
                    "relevance_score": 9.4,
                    "llm_summary": "A strong keynote image.",
                },
                {
                    "people": ["crowd"],
                    "objects": ["chairs"],
                    "scene": "audience",
                    "emotion": "calm",
                    "quality": "medium",
                    "composition": "wide shot",
                    "relevance_score": 6.2,
                    "llm_summary": "A useful supporting image.",
                },
            ]
        ),
        max_selected_images=1,
    )

    analyses, selected = agent.analyze([first, second], "Energetic event recap")

    assert len(analyses) == 2
    assert selected == [first]
