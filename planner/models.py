"""Core domain models for events and selected viewpoints."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Event:
    name: str
    location: str
    radius_km: float = 8.0


@dataclass(frozen=True)
class Viewpoint:
    name: str
    longitude: float
    latitude: float
    view_score: int
    comfort_score: int
    category: str
    notes: str

    @property
    def overall_score(self) -> float:
        return round((self.view_score + self.comfort_score) / 2, 1)


@dataclass(frozen=True)
class Amenity:
    """A mapped facility useful while waiting at an outdoor event."""

    osm_type: str
    osm_id: int
    category: str
    name: str
    longitude: float
    latitude: float
    tags: dict[str, str]
