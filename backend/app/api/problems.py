"""
problems.py — REST API: problem metadata + complexity targets.

GET /api/problems/{slug}
    → Full problem info with per-tier complexity targets
    → 404 if not in DB (problem not seeded yet)

GET /api/problems/
    → List all seeded problem slugs
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.crud import get_problem_by_slug, list_all_slugs
from app.db.models import Problem

router = APIRouter(prefix="/api/problems", tags=["problems"])


def _serialize_problem(problem: Problem) -> dict:
    """Convert ORM Problem → JSON-serialisable dict."""
    targets_by_tier: dict[str, dict] = {}
    for ct in problem.complexity_targets:
        targets_by_tier[ct.tier] = {
            "time_complexity":  ct.time_complexity,
            "space_complexity": ct.space_complexity,
            "approach_name":    ct.approach_name,
            "description":      ct.description,
        }

    return {
        "slug":               problem.slug,
        "title":              problem.title,
        "difficulty":         problem.difficulty,
        "category":           problem.category,
        "complexity_targets": targets_by_tier,
    }


@router.get("/", summary="List all seeded problem slugs")
async def list_problems(db: AsyncSession = Depends(get_db)):
    slugs = await list_all_slugs(db)
    return {"count": len(slugs), "slugs": slugs}


@router.get("/{slug}", summary="Get problem metadata + complexity targets by slug")
async def get_problem(slug: str, db: AsyncSession = Depends(get_db)):
    problem = await get_problem_by_slug(db, slug)
    if not problem:
        raise HTTPException(
            status_code=404,
            detail=f"Problem '{slug}' not found in database. "
                   "It may not be seeded yet."
        )
    return _serialize_problem(problem)
