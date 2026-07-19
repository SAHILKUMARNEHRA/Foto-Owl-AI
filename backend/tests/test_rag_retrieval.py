from backend.rag.retriever import RagRetriever


class RecordingVectorStore:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, int]] = []

    def query(self, collection_name: str, query_text: str, n_results: int = 4):
        self.calls.append((collection_name, query_text, n_results))
        return [{"text": f"match from {collection_name}"}]


def test_rag_retriever_queries_expected_collections() -> None:
    store = RecordingVectorStore()
    retriever = RagRetriever(vector_store=store)  # type: ignore[arg-type]

    style_hits = retriever.retrieve_styles("cinematic recap")
    doc_hits = retriever.retrieve_remotion_docs("Sequence fade transitions")

    assert style_hits[0]["text"] == "match from styles"
    assert doc_hits[0]["text"] == "match from remotion_docs"
    assert store.calls[0][0] == "styles"
    assert store.calls[1][0] == "remotion_docs"
