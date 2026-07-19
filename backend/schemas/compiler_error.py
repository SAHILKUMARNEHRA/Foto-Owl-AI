from __future__ import annotations

from pydantic import BaseModel, Field


class CompilerIssue(BaseModel):
    file: str
    line: int | None = None
    column: int | None = None
    code: str | None = None
    message: str
    raw: str


class CompileResult(BaseModel):
    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int
    issues: list[CompilerIssue] = Field(default_factory=list)
