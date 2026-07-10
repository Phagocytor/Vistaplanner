"""Small, dependency-free client for OpenStreetMap's Overpass API."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from planner.models import Amenity

DEFAULT_ENDPOINT = "https://overpass-api.de/api/interpreter"
FEATURE_TAGS: dict[str, tuple[str, str]] = {
    "toilets": ("amenity", "toilets"),
    "drinking_water": ("amenity", "drinking_water"),
    "bench": ("amenity", "bench"),
    "picnic_table": ("leisure", "picnic_table"),
    "park": ("leisure", "park"),
    "garden": ("leisure", "garden"),
    "bicycle_rental": ("amenity", "bicycle_rental"),
}
TRANSPORT_TAGS: dict[str, tuple[str, str]] = {
    "station": ("railway", "station"),
    "metro_entrance": ("railway", "subway_entrance"),
    "tram_stop": ("railway", "tram_stop"),
    "bus_stop": ("highway", "bus_stop"),
}
AREA_FEATURES = {"park", "garden", "station"}


class OverpassError(RuntimeError):
    """Raised when a public Overpass endpoint cannot fulfil a request."""


def build_query(
    latitude: float,
    longitude: float,
    radius_metres: int,
    feature_tags: dict[str, tuple[str, str]] = FEATURE_TAGS,
) -> str:
    """Return a limited around-query covering practical event amenities."""
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("Coordinates must be valid latitude/longitude values.")
    if not 50 <= radius_metres <= 10_000:
        raise ValueError("Radius must be between 50 and 10,000 metres.")
    selectors = "\n".join(
        f'  {"nwr" if name in AREA_FEATURES else "node"}'
        f'["{key}"="{value}"](around:{radius_metres},{latitude},{longitude});'
        for name, (key, value) in feature_tags.items()
    )
    return f"[out:json][timeout:30];\n(\n{selectors}\n);\nout center tags;"


def parse_elements(
    payload: dict[str, Any],
    feature_tags: dict[str, tuple[str, str]] = FEATURE_TAGS,
) -> list[Amenity]:
    """Convert Overpass JSON elements to points, discarding geometry without a centre."""
    amenities: list[Amenity] = []
    for element in payload.get("elements", []):
        tags = {str(key): str(value) for key, value in element.get("tags", {}).items()}
        category = next(
            (
                name
                for name, (key, value) in feature_tags.items()
                if tags.get(key) == value
            ),
            None,
        )
        coordinates = _coordinates(element)
        if category is None or coordinates is None:
            continue
        latitude, longitude = coordinates
        amenities.append(
            Amenity(
                osm_type=str(element["type"]),
                osm_id=int(element["id"]),
                category=category,
                name=tags.get("name", category.replace("_", " ").title()),
                longitude=longitude,
                latitude=latitude,
                tags=tags,
            )
        )
    return amenities


def _coordinates(element: dict[str, Any]) -> tuple[float, float] | None:
    if "lat" in element and "lon" in element:
        return float(element["lat"]), float(element["lon"])
    centre = element.get("center")
    if isinstance(centre, dict) and "lat" in centre and "lon" in centre:
        return float(centre["lat"]), float(centre["lon"])
    return None


class OverpassClient:
    def __init__(
        self,
        endpoint: str = DEFAULT_ENDPOINT,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        self.endpoint = endpoint
        self.opener = opener

    def scan(
        self,
        latitude: float,
        longitude: float,
        radius_metres: int,
        feature_tags: dict[str, tuple[str, str]] = FEATURE_TAGS,
    ) -> list[Amenity]:
        query = build_query(latitude, longitude, radius_metres, feature_tags)
        data = urlencode({"data": query}).encode("utf-8")
        request = Request(
            self.endpoint,
            data=data,
            headers={"User-Agent": "VistaPlanner/0.1 (+https://github.com/)"},
        )
        try:
            with self.opener(request, timeout=45) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
            raise OverpassError(f"Overpass request failed: {error}") from error
        return parse_elements(payload, feature_tags)
