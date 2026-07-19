from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from backend.renderer.render import RemotionRenderer
from backend.schemas.compiler_error import CompileResult, CompilerIssue


class FakeTextClient:
    def __init__(self, json_responses: list[dict[str, Any]] | None = None, text_responses: list[str] | None = None) -> None:
        self.json_responses = json_responses or []
        self.text_responses = text_responses or []
        self.calls: list[tuple[str, str, str]] = []

    def invoke_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        self.calls.append(("json", system_prompt, user_prompt))
        if not self.json_responses:
            raise AssertionError("No fake JSON responses left.")
        return self.json_responses.pop(0)

    def invoke_text(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append(("text", system_prompt, user_prompt))
        if not self.text_responses:
            raise AssertionError("No fake text responses left.")
        return self.text_responses.pop(0)


class FakeVisionClient:
    def __init__(self, responses: Iterable[dict[str, Any]]) -> None:
        self.responses = list(responses)

    def analyze_image(self, image_path: Path, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        if not self.responses:
            raise AssertionError("No fake vision responses left.")
        return self.responses.pop(0)


class FakeRetriever:
    def __init__(self, styles: list[dict[str, str]] | None = None, docs: list[dict[str, str]] | None = None) -> None:
        self.styles = styles or []
        self.docs = docs or []

    def retrieve_styles(self, query: str, limit: int = 3) -> list[dict[str, str]]:
        return self.styles[:limit]

    def retrieve_remotion_docs(self, query: str, limit: int = 4) -> list[dict[str, str]]:
        return self.docs[:limit]


class FakeCompiler:
    def __init__(self, results: list[CompileResult]) -> None:
        self.results = results

    def compile(self) -> CompileResult:
        if not self.results:
            raise AssertionError("No fake compile results left.")
        return self.results.pop(0)


class FakeRenderer(RemotionRenderer):
    def __init__(self) -> None:
        self.rendered_outputs: list[Path] = []

    def render(self, output_path: Path) -> str:
        output_path.write_text("fake-mp4-binary", encoding="utf-8")
        self.rendered_outputs.append(output_path)
        return "render ok"


def compile_error(message: str) -> CompileResult:
    return CompileResult(
        success=False,
        exit_code=1,
        stderr=message,
        issues=[
            CompilerIssue(
                file="src/generated/GeneratedVideo.tsx",
                line=5,
                column=10,
                code="TS1005",
                message=message,
                raw=message,
            )
        ],
    )
