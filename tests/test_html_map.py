import tempfile
import unittest
from pathlib import Path

from planner.exporters.html_map import write_html_map
from planner.models import Amenity, Event, Viewpoint


class HtmlMapTests(unittest.TestCase):
    def test_writes_leaflet_map_with_all_layers(self):
        viewpoint = Viewpoint("Spot", 2.29, 48.85, 8, 7, "premium", "Test")
        amenity = Amenity("node", 1, "toilets", "WC", 2.3, 48.86, {})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "map.html"
            write_html_map(path, Event("Event", "Paris"), [viewpoint], [amenity], [amenity])
            content = path.read_text(encoding="utf-8")
        self.assertIn("leaflet", content)
        self.assertIn("Points de vue", content)
        self.assertIn("Équipements", content)
        self.assertIn("Transports", content)
