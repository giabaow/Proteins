"""
Embedded ChromaDB - runs in-process, persists to disk, no separate server.
Holds the RAW TEXT side of the data (chunked source pages), keyed by company +
source URL so we can trace every claim back to where it came from.

chromadb (and its onnxruntime dependency) is heavy, so it is imported lazily -
the app boots and serves the frontend + the DB-backed /api routes without it;
only add_chunks() / query_evidence() pull it in.
"""
from __future__ import annotations

from app.config import settings

_collection = None


def _get_collection():
    global _collection
    if _collection is None:
        import chromadb  # noqa: PLC0415 - deliberate lazy import

        client = chromadb.PersistentClient(path=settings.chroma_path)
        _collection = client.get_or_create_collection("proteins1_research")
    return _collection


def add_chunks(
    company: str,
    source_url: str,
    chunks: list[str],
    topic: str = "",
    record_type: str = "opportunity",
) -> None:
    if not chunks:
        return
    ids = [f"{record_type}_{company}_{abs(hash(source_url))}_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "company": company,
            "source_url": source_url,
            "chunk_index": i,
            "topic": topic,
            "record_type": record_type,
        }
        for i in range(len(chunks))
    ]
    # Upsert makes a retry safe when a prior run fetched and stored chunks but
    # failed later during LLM extraction.
    _get_collection().upsert(ids=ids, documents=chunks, metadatas=metadatas)


def query_evidence(query: str, company: str | None = None, n_results: int = 3):
    where = {"company": company} if company else None
    results = _get_collection().query(query_texts=[query], n_results=n_results, where=where)
    out = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]
    for doc, meta, dist in zip(docs, metas, dists):
        out.append({"text": doc, "source_url": meta.get("source_url"), "company": meta.get("company"), "distance": dist})
    return out
