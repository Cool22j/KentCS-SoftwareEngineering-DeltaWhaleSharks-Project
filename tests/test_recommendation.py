import json
import unittest
from unittest.mock import MagicMock, patch

from groq_client import parse_json_response
import recommendation as r


class Cursor(list):
    def sort(self, *args, **kwargs):
        return self

    def limit(self, n):
        return Cursor(self[:n])


class RecommendationTests(unittest.TestCase):
    def test_parse_json_response_extracts_query_and_output(self):
        raw = '```json\n{"query": "Searching for control cards", "output": {"type_line": "Instant"}}\n```'
        parsed = parse_json_response(raw)
        self.assertEqual(parsed["query"], "Searching for control cards")
        self.assertEqual(parsed["output"], {"type_line": "Instant"})

    def test_parse_json_response_rejects_missing_keys(self):
        with self.assertRaises(ValueError):
            parse_json_response('{"only_query": "test"}')

    def test_validate_filter_blocks_unsafe_operators(self):
        with self.assertRaises(ValueError):
            r.validate_filter({"$where": "this.cmc < 3"})

        valid = {"oracle_text": {"$regex": "counter target", "$options": "i"}}
        self.assertEqual(r.validate_filter(valid), valid)

    def test_chain_runs_multiple_searches_and_builds_60_card_deck(self):
        control_cards = [
            {
                "name": f"Control Spell {i}",
                "mana_cost": "{1}{U}",
                "cmc": 2,
                "type_line": "Instant",
                "oracle_text": "Counter target spell.",
                "color_identity": ["U"],
                "legalities": {"modern": "legal"},
            }
            for i in range(5)
        ]
        aggro_cards = [
            {
                "name": f"Aggro Creature {i}",
                "mana_cost": "{R}",
                "cmc": 1,
                "type_line": "Creature — Goblin",
                "oracle_text": "Haste",
                "color_identity": ["R"],
                "legalities": {"modern": "legal"},
            }
            for i in range(5)
        ]

        collection = MagicMock()
        collection.find.side_effect = [
            Cursor(control_cards),
            Cursor(aggro_cards),
        ]

        llm_responses = [
            # Step 1: Plan sub-searches
            {
                "query": "Build an Izzet control and aggro deck",
                "output": {
                    "colors": ["U", "R"],
                    "searches": ["control counterspells", "aggro haste creatures"],
                },
            },
            # Step 2a: Query for control
            {
                "query": "Searching for blue counterspells",
                "output": {"oracle_text": {"$regex": "counter target", "$options": "i"}},
            },
            # Step 2b: Query for aggro
            {
                "query": "Searching for red haste creatures",
                "output": {"oracle_text": {"$regex": "haste", "$options": "i"}},
            },
            # Step 3: Select cards from combined results
            {
                "query": "Mix early red threats with blue disruption",
                "output": {
                    "cards": [
                        {"name": f"Control Spell {i}", "qty": 4, "role": "control"}
                        for i in range(5)
                    ]
                    + [
                        {"name": f"Aggro Creature {i}", "qty": 4, "role": "aggro"}
                        for i in range(4)
                    ]
                },
            },
        ]

        with (
            patch.dict("os.environ", {"GROQ_API_KEY": "test_key"}),
            patch.object(r, "get_cards_collection", return_value=collection),
            patch.object(r, "ask_groq_json", side_effect=llm_responses),
        ):
            deck = r.get_recommendations("I want a deck with both control and aggro", format="modern")

        self.assertEqual(deck["total_cards"], 60)
        self.assertEqual(deck["colors"], ["R", "U"])
        self.assertEqual(
            deck["search_logs"],
            ["Searching for blue counterspells", "Searching for red haste creatures"],
        )
        lands = [c for c in deck["cards"] if c.get("role") == "land"]
        self.assertEqual(sum(c["qty"] for c in lands), 24)


if __name__ == "__main__":
    unittest.main()
