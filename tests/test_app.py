import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest


class DeckBuilderUITests(unittest.TestCase):
    def test_generate_and_save_deck(self):
        fake_deck = {
            "strategy": "Mix of control and aggro",
            "search_logs": ["Searching for control cards", "Searching for aggro cards"],
            "cards": [
                {"name": "Lightning Bolt", "qty": 4, "role": "aggro"},
                {"name": "Counterspell", "qty": 4, "role": "control"},
                {"name": "Mountain", "qty": 26, "role": "land"},
                {"name": "Island", "qty": 26, "role": "land"},
            ],
            "format": "modern",
            "colors": ["R", "U"],
            "total_cards": 60,
        }

        with (
            patch("recommendation.get_recommendations", return_value=fake_deck),
            patch("database.save_deck", return_value="deck123") as save_mock,
        ):
            at = AppTest.from_file("../app.py").run()
            at.text_input[0].set_value("Izzet Tempo")
            at.text_area[0].set_value("Control and aggro")
            at.button[0].click().run()

            self.assertFalse(at.error)
            self.assertTrue(any("60-card deck" in s.value for s in at.success))

            # Click Save Deck
            save_buttons = [b for b in at.button if b.label == "Save Deck"]
            self.assertEqual(len(save_buttons), 1)
            save_buttons[0].click().run()
            save_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
