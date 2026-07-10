"""KML export compatible with Google My Maps and Google Earth."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET

from planner.models import Event, Viewpoint

KML_NAMESPACE = "http://www.opengis.net/kml/2.2"
ET.register_namespace("", KML_NAMESPACE)


def _tag(name: str) -> str:
    return f"{{{KML_NAMESPACE}}}{name}"


def write_kml(path: Path, event: Event, viewpoints: Iterable[Viewpoint]) -> None:
    root = ET.Element(_tag("kml"))
    document = ET.SubElement(root, _tag("Document"))
    ET.SubElement(document, _tag("name")).text = event.name

    for point in viewpoints:
        placemark = ET.SubElement(document, _tag("Placemark"))
        ET.SubElement(placemark, _tag("name")).text = point.name
        description = (
            f"Category: {point.category}\nView: {point.view_score}/10\n"
            f"Comfort: {point.comfort_score}/10\n{point.notes}"
        )
        ET.SubElement(placemark, _tag("description")).text = description
        point_element = ET.SubElement(placemark, _tag("Point"))
        ET.SubElement(point_element, _tag("coordinates")).text = f"{point.longitude},{point.latitude},0"

    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)

