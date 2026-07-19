from __future__ import annotations

import re
import subprocess
from pathlib import Path

from backend.schemas.compiler_error import CompileResult, CompilerIssue

TS_ERROR_PATTERN = re.compile(
    r"^(?P<file>.+)\((?P<line>\d+),(?P<column>\d+)\): error (?P<code>TS\d+): (?P<message>.+)$"
)


class RemotionCompiler:
    def __init__(self, frontend_dir: Path) -> None:
        self._frontend_dir = frontend_dir

    def compile(self) -> CompileResult:
        completed = subprocess.run(
            ["npm", "run", "typecheck"],
            cwd=self._frontend_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        issues = self._parse_issues(completed.stdout + "\n" + completed.stderr)
        return CompileResult(
            success=completed.returncode == 0,
            stdout=completed.stdout,
            stderr=completed.stderr,
            exit_code=completed.returncode,
            issues=issues,
        )

    @staticmethod
    def _parse_issues(output: str) -> list[CompilerIssue]:
        issues: list[CompilerIssue] = []
        for line in output.splitlines():
            match = TS_ERROR_PATTERN.match(line.strip())
            if not match:
                continue
            groups = match.groupdict()
            issues.append(
                CompilerIssue(
                    file=groups["file"],
                    line=int(groups["line"]),
                    column=int(groups["column"]),
                    code=groups["code"],
                    message=groups["message"],
                    raw=line,
                )
            )
        return issues
