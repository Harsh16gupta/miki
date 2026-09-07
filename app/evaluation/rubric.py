"""Typed loader for evaluation rubric configs (Phase 11)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

RUBRICS_DIR = Path(__file__).resolve().parent.parent.parent / "rubrics"
NORMAL_RUBRIC_PATH = RUBRICS_DIR / "normal_interview.yaml"


class RubricDimension(BaseModel):
    """One scored dimension with evidence-anchored bands."""

    name: str
    description: str
    low: str
    medium: str
    high: str


class Rubric(BaseModel):
    """Typed view of one rubric file."""

    version: str = Field(description="Manual semver, bumped on any change")
    mode: str = "normal"
    scale_min: int = 1
    scale_max: int = 5
    dimensions: list[RubricDimension]


def load_rubric(path: Path | str = NORMAL_RUBRIC_PATH) -> Rubric:
    """Parse a rubric YAML file into a validated ``Rubric``."""
    path = Path(path)
    with open(path) as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Rubric file is not a mapping: {path}")
    return Rubric(**data)


@lru_cache(maxsize=1)
def get_normal_rubric() -> Rubric:
    """Cached accessor for the normal-interview rubric (V1 has one mode)."""
    return load_rubric(NORMAL_RUBRIC_PATH)
