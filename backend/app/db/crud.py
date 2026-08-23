"""
crud.py - Async CRUD operations for the DB layer.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ComplexityTarget, Problem


async def get_problem_by_slug(db: AsyncSession, slug: str) -> Problem | None:
    """Fetch a problem and its complexity targets by slug."""
    result = await db.execute(
        select(Problem).where(Problem.slug == slug)
    )
    return result.scalar_one_or_none()


async def get_complexity_for_tier(
    db: AsyncSession,
    slug: str,
    tier: str,
) -> ComplexityTarget | None:
    """Fetch a single complexity target for a given problem slug + tier."""
    result = await db.execute(
        select(ComplexityTarget)
        .join(Problem)
        .where(Problem.slug == slug, ComplexityTarget.tier == tier)
    )
    return result.scalar_one_or_none()


async def upsert_problem(db: AsyncSession, data: dict) -> Problem:
    """
    Insert a problem and its complexity targets.
    If the problem already exists (by slug), skip silently.
    """
    existing = await get_problem_by_slug(db, data["slug"])
    if existing:
        return existing

    problem = Problem(
        slug=data["slug"],
        title=data["title"],
        difficulty=data["difficulty"],
        category=data.get("category", ""),
    )
    db.add(problem)
    await db.flush()  # get problem.id before adding children

    for ct in data.get("complexity_targets", []):
        db.add(ComplexityTarget(
            problem_id=problem.id,
            tier=ct["tier"],
            time_complexity=ct["time_complexity"],
            space_complexity=ct.get("space_complexity", "O(N)"),
            approach_name=ct.get("approach_name", ""),
            description=ct.get("description", ""),
        ))

    await db.commit()
    await db.refresh(problem)
    return problem


async def list_all_slugs(db: AsyncSession) -> list[str]:
    """Return all seeded problem slugs."""
    result = await db.execute(select(Problem.slug))
    return [row[0] for row in result.fetchall()]
