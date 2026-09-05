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
from typing import Any

from fastembed import TextEmbedding
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
VECTOR_SIZE = 384   # fastembed BAAI/bge-small-en-v1.5 vector size

_client: QdrantClient | None = None
_embedder: TextEmbedding | None = None


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

    # Initialize FastEmbed
    global _embedder
    _embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    # Load model into memory
    list(_embedder.embed(["warmup"]))

    print(f"[Qdrant] Ready  ({mode}) + FastEmbed loaded")


def close_qdrant() -> None:
    global _client
    if _client:
        _client.close()
        _client = None
        print("[Qdrant] Closed.")


def delete_hint(point_id: str) -> bool:
    """
    Delete a hint vector from Qdrant by its point_id (SHA-256 req_hash).
    Returns True if successfully deleted, False otherwise.
    """
    client = get_qdrant()
    try:
        numeric_id = int(point_id[:15], 16)
        client.delete(
            collection_name=COLLECTION,
            points_selector=[numeric_id],
        )
        print(f"[Qdrant] Deleted hint {point_id[:8]}...")
        return True
    except Exception as exc:
        print(f"[Qdrant] Delete failed for {point_id[:8]}: {exc}")
        return False


# ── Embedding ─────────────────────────────────────────────────────────────────

def _embed(text: str) -> list[float]:
    """
    Phase 4: Real semantic text embedding using FastEmbed (BAAI/bge-small-en-v1.5).
    """
    global _embedder
    if _embedder is None:
        raise RuntimeError("FastEmbed not initialized. Call init_qdrant() first.")
    
    # embed() returns a generator of numpy arrays, we want the first one as a list of floats
    result = list(_embedder.embed([text]))[0]
    return result.tolist()


# ── Store / Retrieve ──────────────────────────────────────────────────────────

def store_hint(
    point_id: str,
    text: str,
    code_context: str,
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
                vector=_embed(code_context),
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
