import json
import tempfile
import unittest
from pathlib import Path

from planner.providers.geojson import read_amenities_geojson


class GeoJsonProviderTests(unittest.TestCase):
    def test_reads_an_exported_point_feature(self):
        payload = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [2.29, 48.85]},
                    "properties": {"category": "toilets", "osm_type": "node", "osm_id": 1},
                }
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "amenities.geojson"
            path.write_text(json.dumps(payload), encoding="utf-8")
            amenities = read_amenities_geojson(path)
        self.assertEqual("toilets", amenities[0].category)
        self.assertEqual(2.29, amenities[0].longitude)
