from __future__ import annotations

import os
import threading

import chromadb
from sentence_transformers import SentenceTransformer

from config import settings

_lock = threading.Lock()
_chroma_client: chromadb.ClientAPI | None = None

_CHROMA_PATH = os.path.abspath(settings.chroma_db_path)

# Load eagerly in the main thread with an explicit device so background workers
# don't hit the meta-tensor initialisation error.
_model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")


def _embed(text: str) -> list[float]:
    return _model.encode(text, convert_to_numpy=True).tolist()


def _get_collection() -> chromadb.Collection:
    global _chroma_client
    if _chroma_client is None:
        with _lock:
            if _chroma_client is None:
                _chroma_client = chromadb.PersistentClient(path=_CHROMA_PATH)
    # No embedding_function — we pass pre-computed embeddings directly
    return _chroma_client.get_or_create_collection(
        name="minerva_research_cache",
        metadata={"hnsw:space": "cosine"},
    )


def check_cache(query: str) -> tuple[str, list[str]] | None:
    """Return (content, sources) if a similar result is cached, else None.

    Cosine distance: 0 = identical, 1 = completely different.
    A distance below (1 - similarity_threshold) is a hit.
    """
    collection = _get_collection()
    if collection.count() == 0:
        return None

    query_embedding = _embed(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=1,
        include=["documents", "metadatas", "distances"],
    )

    distances = results.get("distances", [[]])[0]
    if not distances:
        return None

    distance_threshold = 1.0 - settings.similarity_threshold
    if distances[0] >= distance_threshold:
        return None

    content = results["documents"][0][0]
    metadata = results["metadatas"][0][0]
    sources: list[str] = metadata.get("sources", "").split("\n") if metadata.get("sources") else []
    return content, sources


def store_in_cache(query: str, content: str, sources: list[str]) -> None:
    """Embed and persist a research result keyed by the search query."""
    collection = _get_collection()
    doc_id = f"query_{abs(hash(query))}"
    # Embed the query string (not the content) so that lookup by a similar
    # query finds this entry via vector similarity.
    query_embedding = _embed(query)
    collection.upsert(
        ids=[doc_id],
        documents=[content],
        embeddings=[query_embedding],
        metadatas=[{"query": query, "sources": "\n".join(sources)}],
    )
