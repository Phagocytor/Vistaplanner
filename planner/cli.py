"""Command line entry point for VistaPlanner."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from planner.config import DEFAULT_BASENAME, DEFAULT_OUTPUT_DIRECTORY
from planner.data.viewpoints import PARIS_FIREWORKS_VIEWPOINTS
from planner.exporters.geojson import write_amenities_geojson, write_geojson
from planner.exporters.html_map import write_html_map
from planner.exporters.kml import write_kml
from planner.models import Event
from planner.providers.overpass import (
    DEFAULT_ENDPOINT,
    FEATURE_TAGS,
    TRANSPORT_TAGS,
    OverpassClient,
    OverpassError,
)
from planner.providers.geojson import read_amenities_geojson
from planner.scoring import score_location


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vistaplanner", description="Build portable maps for outdoor events.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build", help="Export the initial curated viewpoint map.")
    build.add_argument("--event", default="Paris fireworks", help="Name of the event.")
    build.add_argument("--location", default="Tour Eiffel", help="Event location.")
    build.add_argument("--radius", type=float, default=8.0, help="Planning radius in kilometres.")
    build.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIRECTORY, help="Directory for exported files.")
    build.add_argument("--basename", default=DEFAULT_BASENAME, help="Name shared by the export files.")
    _add_overpass_arguments(subparsers.add_parser("scan", help="Fetch practical amenities from OpenStreetMap."))
    _add_overpass_arguments(
        subparsers.add_parser("transport", help="Fetch public-transport features from OpenStreetMap."),
        output=Path("output/transport.geojson"),
    )
    _add_overpass_arguments(
        subparsers.add_parser("score", help="Score mapped comfort and transport access around a point."),
        output=Path("output/location-score.json"),
    )
    score_files = subparsers.add_parser("score-files", help="Score previously exported amenity and transport layers.")
    score_files.add_argument("--amenities", type=Path, required=True, help="Amenity GeoJSON exported by scan.")
    score_files.add_argument("--transport", type=Path, required=True, help="Transport GeoJSON exported by transport.")
    score_files.add_argument("--output", type=Path, default=Path("output/location-score.json"), help="Score report output file.")
    map_command = subparsers.add_parser("map", help="Create an interactive HTML map from exported layers.")
    map_command.add_argument("--event", default="Paris fireworks", help="Name shown on the map.")
    map_command.add_argument("--location", default="Tour Eiffel", help="Event location.")
    map_command.add_argument("--amenities", type=Path, required=True, help="Amenity GeoJSON exported by scan.")
    map_command.add_argument("--transport", type=Path, required=True, help="Transport GeoJSON exported by transport.")
    map_command.add_argument("--output", type=Path, default=Path("output/event-map.html"), help="HTML map output file.")
    return parser


def _add_overpass_arguments(parser: argparse.ArgumentParser, output: Path = Path("output/amenities.geojson")) -> None:
    parser.add_argument("--lat", type=float, required=True, help="Centre latitude.")
    parser.add_argument("--lon", type=float, required=True, help="Centre longitude.")
    parser.add_argument("--radius", type=int, default=800, help="Search radius in metres (50–10,000).")
    parser.add_argument("--output", type=Path, default=output, help="GeoJSON output file.")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="Overpass API endpoint.")


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "map":
        try:
            amenities = read_amenities_geojson(args.amenities)
            transport = read_amenities_geojson(args.transport)
        except ValueError as error:
            parser.error(str(error))
        event = Event(name=args.event, location=args.location)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        write_html_map(args.output, event, PARIS_FIREWORKS_VIEWPOINTS, amenities, transport)
        print(f"Interactive map: {args.output}")
        return
    if args.command == "score-files":
        try:
            result = score_location(read_amenities_geojson(args.amenities), read_amenities_geojson(args.transport))
        except ValueError as error:
            parser.error(str(error))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Comfort: {result.comfort}/10 | Access: {result.access}/10 | Overall: {result.overall}/10")
        print(f"Score report: {args.output}")
        return
    if args.command == "score":
        try:
            client = OverpassClient(endpoint=args.endpoint)
            amenities = client.scan(args.lat, args.lon, args.radius, feature_tags=FEATURE_TAGS)
            transport = client.scan(args.lat, args.lon, args.radius, feature_tags=TRANSPORT_TAGS)
        except (OverpassError, ValueError) as error:
            parser.error(str(error))
        result = score_location(amenities, transport)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Comfort: {result.comfort}/10 | Access: {result.access}/10 | Overall: {result.overall}/10")
        print(f"Score report: {args.output}")
        return
    if args.command in {"scan", "transport"}:
        try:
            feature_tags = TRANSPORT_TAGS if args.command == "transport" else FEATURE_TAGS
            amenities = OverpassClient(endpoint=args.endpoint).scan(
                args.lat,
                args.lon,
                args.radius,
                feature_tags=feature_tags,
            )
        except (OverpassError, ValueError) as error:
            parser.error(str(error))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        write_amenities_geojson(args.output, amenities)
        label = "transport features" if args.command == "transport" else "mapped amenities"
        print(f"Exported {len(amenities)} {label} to {args.output}")
        return
    if args.command != "build":
        return
    event = Event(name=args.event, location=args.location, radius_km=args.radius)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    kml_path = args.output_dir / f"{args.basename}.kml"
    geojson_path = args.output_dir / f"{args.basename}.geojson"
    write_kml(kml_path, event, PARIS_FIREWORKS_VIEWPOINTS)
    write_geojson(geojson_path, event, PARIS_FIREWORKS_VIEWPOINTS)
    print(f"Exported {len(PARIS_FIREWORKS_VIEWPOINTS)} viewpoints")
    print(f"KML: {kml_path}")
    print(f"GeoJSON: {geojson_path}")
