"""
qdrant_store.py — Qdrant vector store (in-memory dev, server in prod).

Dev:  QdrantClient(":memory:")         — no server needed
Prod: QdrantClient(url=QDRANT_URL)     — set QDRANT_URL in .env

Collection: coach_hints
Vectors: 128-dim hash embeddings (Phase 3 stub; real embeddings in Phase 4)
Payload:  { problem_slug, tier, hint_level, text }
"""
from __future__ import annotations
import hashlib
import struct
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
)

from app.config import settings

COLLECTION  = "coach_hints"
VECTOR_SIZE = 128   # Phase 4 will raise this to match the real embedding model

_client: QdrantClient | None = None


def get_qdrant() -> QdrantClient:
    global _client
    if _client is None:
        raise RuntimeError("Qdrant not initialised. Call init_qdrant() first.")
    return _client


def init_qdrant() -> None:
    """Initialise Qdrant client and create collection if needed."""
    global _client
    if settings.qdrant_url:
        _client = QdrantClient(url=settings.qdrant_url)
        mode = f"server ({settings.qdrant_url})"
    else:
        _client = QdrantClient(":memory:")
        mode = "in-memory"

    # Create collection if it doesn't exist
    existing = {c.name for c in _client.get_collections().collections}
    if COLLECTION not in existing:
        _client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )

    print(f"[Qdrant] Ready  ({mode})")


def close_qdrant() -> None:
    global _client
    if _client:
        _client.close()
        _client = None
        print("[Qdrant] Closed.")


# ── Embedding ─────────────────────────────────────────────────────────────────

def _embed(text: str) -> list[float]:
    """
    Phase 3 stub: deterministic 128-dim vector from SHA-256 rolling hash.
    Not semantically meaningful — replaced by real model in Phase 4.
    """
    digest = hashlib.sha256(text.encode()).digest()
    # Tile digest bytes to fill 128 floats (each float from 2 bytes)
    extended = (digest * 8)[:256]   # 256 bytes
    floats = [
        struct.unpack("H", extended[i*2:(i*2)+2])[0] / 65535.0
        for i in range(VECTOR_SIZE)
    ]
    return floats


# ── Store / Retrieve ──────────────────────────────────────────────────────────

def store_hint(
    point_id: str,
    text: str,
    problem_slug: str,
    tier: str,
    hint_level: int | None,
) -> None:
    """
    Upsert a hint vector into Qdrant.
    point_id should be the SHA-256 hash of the request (cache key).
    """
    client = get_qdrant()
    # Convert hex hash to int for Qdrant point ID
    numeric_id = int(point_id[:15], 16)  # use first 15 hex chars → fits in int64

    client.upsert(
        collection_name=COLLECTION,
        points=[
            PointStruct(
                id=numeric_id,
                vector=_embed(text),
                payload={
                    "problem_slug": problem_slug,
                    "tier": tier,
                    "hint_level": hint_level,
                    "text": text[:500],  # truncate for payload efficiency
                },
            )
        ],
    )


def search_similar_hints(
    query_text: str,
    problem_slug: str | None = None,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """
    Find the most similar stored hints to query_text.
    Optionally filter by problem_slug.
    Returns list of { score, text, tier, hint_level }.
    """
    client = get_qdrant()
    query_filter = None
    if problem_slug:
        query_filter = Filter(
            must=[FieldCondition(key="problem_slug", match=MatchValue(value=problem_slug))]
        )

    response = client.query_points(
        collection_name=COLLECTION,
        query=_embed(query_text),
        query_filter=query_filter,
        limit=limit,
        with_payload=True,
    )

    return [
        {
            "score": hit.score,
            "text":  hit.payload.get("text", ""),
            "tier":  hit.payload.get("tier", ""),
            "hint_level": hit.payload.get("hint_level"),
        }
        for hit in response.points
    ]
