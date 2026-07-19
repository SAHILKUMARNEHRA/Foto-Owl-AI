from __future__ import annotations

from dataclasses import dataclass

from backend.rag.vector_store import ChromaVectorStore


@dataclass(slots=True)
class RagRetriever:
    vector_store: ChromaVectorStore

    def retrieve_styles(self, query: str, limit: int = 3) -> list[dict[str, str]]:
        return self.vector_store.query(collection_name="styles", query_text=query, n_results=limit)

    def retrieve_remotion_docs(self, query: str, limit: int = 4) -> list[dict[str, str]]:
        return self.vector_store.query(collection_name="remotion_docs", query_text=query, n_results=limit)
