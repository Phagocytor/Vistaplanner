import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from planner.cli import main


class ExportTests(unittest.TestCase):
    def test_build_creates_two_valid_exports(self):
        with tempfile.TemporaryDirectory() as directory:
            output_directory = Path(directory)
            main(["build", "--output-dir", str(output_directory), "--basename", "test-map"])

            kml_path = output_directory / "test-map.kml"
            geojson_path = output_directory / "test-map.geojson"
            self.assertTrue(kml_path.exists())
            self.assertTrue(geojson_path.exists())
            self.assertEqual(10, len(ET.parse(kml_path).findall(".//{http://www.opengis.net/kml/2.2}Placemark")))
            payload = json.loads(geojson_path.read_text(encoding="utf-8"))
            self.assertEqual("FeatureCollection", payload["type"])
            self.assertEqual(10, len(payload["features"]))
