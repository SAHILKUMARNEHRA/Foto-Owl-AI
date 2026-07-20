from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.rag.vector_store import ChromaVectorStore


def chunk_markdown(text: str, chunk_size: int = 700) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= chunk_size:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = paragraph
    if current:
        chunks.append(current)
    return chunks


@dataclass(slots=True)
class RagRetriever:
    vector_store: "ChromaVectorStore"

    def retrieve_styles(self, query: str, limit: int = 3) -> list[dict[str, str]]:
        return self.vector_store.query(collection_name="styles", query_text=query, n_results=limit)

    def retrieve_remotion_docs(self, query: str, limit: int = 4) -> list[dict[str, str]]:
        return self.vector_store.query(collection_name="remotion_docs", query_text=query, n_results=limit)


@dataclass(slots=True)
class FileRetriever:
    docs_dir: Path

    def retrieve_styles(self, query: str, limit: int = 3) -> list[dict[str, str]]:
        return self._retrieve(directory=self.docs_dir / "styles", collection="styles", limit=limit)

    def retrieve_remotion_docs(self, query: str, limit: int = 4) -> list[dict[str, str]]:
        return self._retrieve(directory=self.docs_dir / "remotion", collection="remotion_docs", limit=limit)

    def _retrieve(self, directory: Path, collection: str, limit: int) -> list[dict[str, str]]:
        docs: list[dict[str, str]] = []
        for markdown_file in sorted(directory.glob("*.md")):
            for chunk in chunk_markdown(markdown_file.read_text(encoding="utf-8")):
                docs.append({"text": chunk, "source": markdown_file.name, "collection": collection})
                if len(docs) >= limit:
                    return docs
        return docs
