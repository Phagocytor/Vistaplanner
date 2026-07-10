import unittest

from planner.providers.overpass import TRANSPORT_TAGS, build_query, parse_elements


class OverpassTests(unittest.TestCase):
    def test_build_query_contains_all_expected_filters(self):
        query = build_query(48.8584, 2.2945, 800)
        self.assertIn('"amenity"="toilets"', query)
        self.assertIn('"leisure"="park"', query)
        self.assertIn('node["amenity"="toilets"]', query)
        self.assertIn('nwr["leisure"="park"]', query)
        self.assertIn("around:800,48.8584,2.2945", query)

    def test_parse_elements_uses_node_and_way_centres(self):
        payload = {
            "elements": [
                {"type": "node", "id": 1, "lat": 48.85, "lon": 2.29, "tags": {"amenity": "toilets"}},
                {
                    "type": "way",
                    "id": 2,
                    "center": {"lat": 48.86, "lon": 2.30},
                    "tags": {"leisure": "park", "name": "Parc"},
                },
            ]
        }
        amenities = parse_elements(payload)
        self.assertEqual(
            [("toilets", "Toilets"), ("park", "Parc")],
            [(item.category, item.name) for item in amenities],
        )

    def test_parse_elements_can_use_transport_categories(self):
        payload = {
            "elements": [
                {
                    "type": "node",
                    "id": 3,
                    "lat": 48.85,
                    "lon": 2.29,
                    "tags": {"railway": "subway_entrance"},
                }
            ]
        }
        amenities = parse_elements(payload, TRANSPORT_TAGS)
        self.assertEqual("metro_entrance", amenities[0].category)
