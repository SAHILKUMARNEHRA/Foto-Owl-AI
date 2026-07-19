from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import chromadb
from chromadb.api.models.Collection import Collection


@dataclass(slots=True)
class RagDocument:
    document_id: str
    text: str
    metadata: dict[str, str]


class ChromaVectorStore:
    def __init__(self, persist_directory: Path, embedding_function: object) -> None:
        self._client = chromadb.PersistentClient(path=str(persist_directory))
        self._embedding_function = embedding_function

    def get_or_create_collection(self, name: str) -> Collection:
        return self._client.get_or_create_collection(
            name=name,
            embedding_function=self._embedding_function,
        )

    def upsert_documents(self, collection_name: str, documents: Iterable[RagDocument]) -> None:
        collection = self.get_or_create_collection(collection_name)
        docs = list(documents)
        if not docs:
            return
        collection.upsert(
            ids=[document.document_id for document in docs],
            documents=[document.text for document in docs],
            metadatas=[document.metadata for document in docs],
        )

    def query(self, collection_name: str, query_text: str, n_results: int = 4) -> list[dict[str, str]]:
        collection = self.get_or_create_collection(collection_name)
        results = collection.query(query_texts=[query_text], n_results=n_results)
        response: list[dict[str, str]] = []
        for index, document in enumerate(results.get("documents", [[]])[0]):
            metadata = results.get("metadatas", [[]])[0][index] or {}
            response.append({"text": document, **metadata})
        return response
