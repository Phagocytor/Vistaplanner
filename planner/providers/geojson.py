"""Read VistaPlanner-compatible GeoJSON layers from disk."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from planner.models import Amenity


def read_amenities_geojson(path: Path) -> list[Amenity]:
    """Load point features emitted by :func:`write_amenities_geojson`."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read GeoJSON file {path}: {error}") from error
    if payload.get("type") != "FeatureCollection":
        raise ValueError(f"GeoJSON file {path} is not a FeatureCollection.")
    return [_feature_to_amenity(feature) for feature in payload.get("features", [])]


def _feature_to_amenity(feature: dict[str, Any]) -> Amenity:
    geometry = feature.get("geometry", {})
    properties = feature.get("properties", {})
    coordinates = geometry.get("coordinates", [])
    if geometry.get("type") != "Point" or len(coordinates) < 2:
        raise ValueError("All score input features must be GeoJSON points.")
    return Amenity(
        osm_type=str(properties.get("osm_type", "unknown")),
        osm_id=int(properties.get("osm_id", 0)),
        category=str(properties["category"]),
        name=str(properties.get("name", properties["category"])),
        longitude=float(coordinates[0]),
        latitude=float(coordinates[1]),
        tags={str(key): str(value) for key, value in properties.get("tags", {}).items()},
    )
