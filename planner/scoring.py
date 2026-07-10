"""Transparent, evidence-based scores for event waiting locations."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from planner.models import Amenity


@dataclass(frozen=True)
class ScoreBreakdown:
    comfort: float
    access: float
    overall: float
    counts: dict[str, int]

    def as_dict(self) -> dict[str, object]:
        return {
            "comfort_score": self.comfort,
            "access_score": self.access,
            "overall_score": self.overall,
            "evidence_counts": self.counts,
        }


def _contribution(count: int, saturation: int, maximum: float) -> float:
    return min(count / saturation, 1.0) * maximum


def score_location(amenities: Iterable[Amenity], transport: Iterable[Amenity]) -> ScoreBreakdown:
    """Score mapped comfort and access evidence on a 0–10 scale.

    The result is deliberately limited to what OpenStreetMap can support. It is
    not a safety, visibility, crowd, or event-access prediction.
    """
    counts = Counter(item.category for item in amenities)
    counts.update(item.category for item in transport)
    comfort = (
        _contribution(counts["toilets"], 2, 2.5)
        + _contribution(counts["drinking_water"], 2, 2.5)
        + _contribution(counts["bench"], 10, 1.5)
        + _contribution(counts["park"] + counts["garden"], 2, 1.5)
        + _contribution(counts["picnic_table"], 3, 1.0)
        + _contribution(counts["bicycle_rental"], 2, 1.0)
    )
    access = (
        _contribution(counts["metro_entrance"], 3, 4.0)
        + _contribution(counts["station"], 2, 2.5)
        + _contribution(counts["tram_stop"], 2, 1.5)
        + _contribution(counts["bus_stop"], 5, 2.0)
    )
    comfort = round(min(comfort, 10.0), 1)
    access = round(min(access, 10.0), 1)
    return ScoreBreakdown(
        comfort=comfort,
        access=access,
        overall=round(comfort * 0.6 + access * 0.4, 1),
        counts=dict(sorted(counts.items())),
    )
