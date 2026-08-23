"""
models.py - SQLAlchemy ORM models.

Tables:
  problems           - LeetCode problem metadata
  complexity_targets - Per-tier complexity info per problem
"""
from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Problem(Base):
    __tablename__ = "problems"

    id:         Mapped[int]  = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug:       Mapped[str]  = mapped_column(String(200), unique=True, index=True, nullable=False)
    title:      Mapped[str]  = mapped_column(String(300), nullable=False)
    difficulty: Mapped[str]  = mapped_column(String(10),  nullable=False)  # Easy/Medium/Hard
    category:   Mapped[str]  = mapped_column(String(100), nullable=True)   # Array, DP, Graph...

    complexity_targets: Mapped[list[ComplexityTarget]] = relationship(
        "ComplexityTarget",
        back_populates="problem",
        cascade="all, delete-orphan",
        lazy="selectin",   # auto-load with the problem
    )

    def __repr__(self) -> str:
        return f"<Problem {self.slug!r} [{self.difficulty}]>"


class ComplexityTarget(Base):
    __tablename__ = "complexity_targets"

    id:               Mapped[int]  = mapped_column(Integer, primary_key=True, autoincrement=True)
    problem_id:       Mapped[int]  = mapped_column(ForeignKey("problems.id"), nullable=False)
    tier:             Mapped[str]  = mapped_column(String(20),  nullable=False)  # BRUTE_FORCE / BETTER / OPTIMAL
    time_complexity:  Mapped[str]  = mapped_column(String(50),  nullable=False)  # e.g. "O(N²)"
    space_complexity: Mapped[str]  = mapped_column(String(50),  nullable=True)   # e.g. "O(1)"
    approach_name:    Mapped[str]  = mapped_column(String(100), nullable=True)   # e.g. "Hash Map"
    description:      Mapped[str]  = mapped_column(Text,        nullable=True)

    problem: Mapped[Problem] = relationship("Problem", back_populates="complexity_targets")

    def __repr__(self) -> str:
        return f"<ComplexityTarget [{self.tier}] {self.time_complexity}>"
