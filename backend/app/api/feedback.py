"""
feedback.py — REST endpoint for user hint feedback (thumbs up / thumbs down).

POST /api/feedback
  Body: { "hint_id": "<sha256_hash>", "vote": "up" | "down" }

  - "up"   → do nothing (hint stays in Qdrant)
  - "down" → delete hint vector from Qdrant permanently
"""
from fastapi import APIRouter, HTTPException
from app.schemas import FeedbackRequest
from app.vector.qdrant_store import delete_hint

router = APIRouter(prefix="/api", tags=["feedback"])


@router.post("/feedback")
async def submit_feedback(body: FeedbackRequest):
    """
    Accept user feedback for a generated hint.
    Thumbs down (vote='down') permanently removes the hint from Qdrant
    so it is never retrieved as a RAG example for future users.
    """
    if body.vote == "down":
        success = delete_hint(body.hint_id)
        if not success:
            # Non-fatal — hint may have already expired or never been stored
            raise HTTPException(
                status_code=404,
                detail="Hint not found in vector store or already deleted."
            )
        return {"status": "deleted", "hint_id": body.hint_id}

    # vote == "up": nothing to do — hint already stays in Qdrant
    return {"status": "kept", "hint_id": body.hint_id}
