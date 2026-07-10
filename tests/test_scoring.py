import unittest

from planner.models import Amenity
from planner.scoring import score_location


def amenity(category: str) -> Amenity:
    return Amenity("node", 1, category, category, 2.0, 48.0, {})


class ScoringTests(unittest.TestCase):
    def test_empty_evidence_scores_zero(self):
        result = score_location([], [])
        self.assertEqual(0.0, result.comfort)
        self.assertEqual(0.0, result.access)
        self.assertEqual(0.0, result.overall)

    def test_scores_are_capped_and_evidence_is_exposed(self):
        amenities = [amenity("toilets")] * 4 + [amenity("drinking_water")] * 4 + [amenity("bench")] * 10
        transport = [amenity("metro_entrance")] * 3 + [amenity("station")] * 2 + [amenity("tram_stop")] * 2 + [amenity("bus_stop")] * 5
        result = score_location(amenities, transport)
        self.assertEqual(6.5, result.comfort)
        self.assertEqual(10.0, result.access)
        self.assertEqual(7.9, result.overall)
        self.assertEqual(4, result.counts["toilets"])
