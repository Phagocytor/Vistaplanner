"""GeoJSON export using only the standard library."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from planner.models import Amenity, Event, Viewpoint


def write_geojson(path: Path, event: Event, viewpoints: Iterable[Viewpoint]) -> None:
    features = []
    for point in viewpoints:
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [point.longitude, point.latitude]},
                "properties": {
                    "name": point.name,
                    "event": event.name,
                    "location": event.location,
                    "category": point.category,
                    "view_score": point.view_score,
                    "comfort_score": point.comfort_score,
                    "overall_score": point.overall_score,
                    "notes": point.notes,
                },
            }
        )
    path.write_text(json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False, indent=2), encoding="utf-8")


def write_amenities_geojson(path: Path, amenities: Iterable[Amenity]) -> None:
    """Write OpenStreetMap facilities as a portable GeoJSON feature collection."""
    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [item.longitude, item.latitude]},
            "properties": {
                "name": item.name,
                "category": item.category,
                "osm_type": item.osm_type,
                "osm_id": item.osm_id,
                "tags": item.tags,
            },
        }
        for item in amenities
    ]
    path.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
