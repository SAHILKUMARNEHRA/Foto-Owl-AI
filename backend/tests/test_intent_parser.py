from backend.agents.intent_parser import IntentParserAgent
from backend.tests.fakes import FakeTextClient


def test_intent_parser_returns_structured_intent() -> None:
    agent = IntentParserAgent(
        model_client=FakeTextClient(
            json_responses=[
                {
                    "video_style": "cinematic",
                    "caption_tone": "warm",
                    "pacing": "medium",
                    "transition_style": "fade",
                    "text_overlay": "minimal lower thirds",
                    "animation_style": "slow push-in",
                    "music_mood": "uplifting",
                    "color_palette": "golden blue",
                }
            ]
        )
    )

    result = agent.parse("Create a cinematic event recap with warm captions.")

    assert result.video_style == "cinematic"
    assert result.transition_style == "fade"
