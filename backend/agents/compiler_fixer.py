from __future__ import annotations

from pathlib import Path

from backend.rag.retriever import RagRetriever
from backend.schemas.compiler_error import CompileResult
from backend.utils.files import write_text
from backend.utils.ollama import TextModelClient


class CompilerFixerAgent:
    def __init__(self, model_client: TextModelClient, retriever: RagRetriever) -> None:
        self._model_client = model_client
        self._retriever = retriever

    def fix(
        self,
        script: str,
        compile_result: CompileResult,
        script_path: Path,
        output_copy_path: Path,
    ) -> str:
        query = "\n".join(issue.message for issue in compile_result.issues) or compile_result.stderr
        docs = self._retriever.retrieve_remotion_docs(query=query, limit=5)
        fixed_payload = self._model_client.invoke_json(
            system_prompt=(
                "You fix a Remotion TypeScript file using the provided compiler errors. "
                "Return JSON with exactly one key: corrected_script. "
                "The corrected_script value must be complete TypeScript TSX code with no markdown fences or explanation. "
                "Preserve the intended storyboard and avoid unnecessary rewrites."
            ),
            user_prompt=(
                f"Compiler stderr:\n{compile_result.stderr}\n\n"
                f"Compiler issues:\n{compile_result.model_dump_json(indent=2)}\n\n"
                f"Relevant Remotion docs:\n{docs}\n\n"
                f"Current script:\n{script}"
            ),
        )
        fixed_script = str(fixed_payload["corrected_script"])
        fixed_script = self._sanitize_script(fixed_script)
        write_text(script_path, fixed_script)
        write_text(output_copy_path, fixed_script)
        return fixed_script

    @staticmethod
    def _sanitize_script(script: str) -> str:
        cleaned = script.strip()
        if "```" in cleaned:
            lines = cleaned.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        if not cleaned.startswith(("import ", "const ", "type ", "export ")):
            for marker in ("import ", "const ", "type ", "export default"):
                index = cleaned.find(marker)
                if index != -1:
                    cleaned = cleaned[index:]
                    break

        return cleaned.rstrip() + "\n"
