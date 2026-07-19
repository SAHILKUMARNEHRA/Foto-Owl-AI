from __future__ import annotations

from pathlib import Path
from typing import Iterable

from backend.config import Settings
from backend.rag.vector_store import ChromaVectorStore, RagDocument


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


def _iter_documents(directory: Path, collection: str) -> Iterable[RagDocument]:
    for markdown_file in sorted(directory.glob("*.md")):
        for index, chunk in enumerate(chunk_markdown(markdown_file.read_text(encoding="utf-8"))):
            yield RagDocument(
                document_id=f"{collection}:{markdown_file.stem}:{index}",
                text=chunk,
                metadata={"source": markdown_file.name, "collection": collection},
            )


def seed_vector_store(settings: Settings, vector_store: ChromaVectorStore) -> None:
    styles_dir = settings.docs_dir / "styles"
    remotion_dir = settings.docs_dir / "remotion"
    vector_store.upsert_documents("styles", _iter_documents(styles_dir, "styles"))
    vector_store.upsert_documents("remotion_docs", _iter_documents(remotion_dir, "remotion_docs"))
