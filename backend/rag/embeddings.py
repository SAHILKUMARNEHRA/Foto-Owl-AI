from __future__ import annotations

from typing import Sequence

from langchain_community.embeddings import HuggingFaceBgeEmbeddings


class LocalEmbeddingFunction:
    def __init__(self, model_name: str) -> None:
        self._embeddings = HuggingFaceBgeEmbeddings(
            model_name=model_name,
            encode_kwargs={"normalize_embeddings": True},
        )

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return self._embeddings.embed_documents(list(texts))

    def embed_query(self, text: str) -> list[float]:
        return self._embeddings.embed_query(text)

    def __call__(self, input: Sequence[str]) -> list[list[float]]:
        return self.embed_documents(texts=input)
