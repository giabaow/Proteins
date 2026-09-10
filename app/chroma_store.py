"""
Embedded ChromaDB - runs in-process, persists to disk, no separate server.
Holds the RAW TEXT side of the data (chunked source pages), keyed by company +
source URL so we can trace every claim back to where it came from.
"""
from __future__ import annotations

import chromadb

from app.config import settings

_client = chromadb.PersistentClient(path=settings.chroma_path)
_collection = _client.get_or_create_collection("proteins1_research")


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
    _collection.upsert(ids=ids, documents=chunks, metadatas=metadatas)


def query_evidence(query: str, company: str | None = None, n_results: int = 3):
    where = {"company": company} if company else None
    results = _collection.query(query_texts=[query], n_results=n_results, where=where)
    out = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]
    for doc, meta, dist in zip(docs, metas, dists):
        out.append({"text": doc, "source_url": meta.get("source_url"), "company": meta.get("company"), "distance": dist})
    return out
