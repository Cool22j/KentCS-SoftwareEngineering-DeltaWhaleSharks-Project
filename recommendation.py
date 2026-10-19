import json
import os
import requests

from dotenv import load_dotenv
from database import get_cards_collection, get_decks_collection
from rocky import get_model, ask_rocky


load_dotenv()

CARD_FIELDS = ("id", "name", "mana_cost", "type", "card_text", "colors", "from_guy", "card_faces", "image_on", "prices")
CARD_LIMIT = 100

def _base_projection():
    proj = {field: 1 for field in CARD_FIELDS}
    proj["_id"] = 0
    return proj

def _fetch(query, limit=CARD_LIMIT):
    #a Mongo, returns cards for Rocky
    cards = list(
        get_cards_collection()
        .find(query, _base_projection())
        .sort("name", 1)
        .limit(limit)
    )
    if not cards:
        raise ValueError("No cards match this description")
    return cards


def query_from_filters(format=None, colors=None, card_type=None, max_mana_cost=None):
    query = {"lang": "en"}
    known_formats = {"commander", "legacy", "modern", "pauper", "pioneer", "standard", "vintage"}
    if format and format.lower() in known_formats:
        query[f"legalities.{format.lower()}"] = "legal" 

    if colors:
        query["color_identity"] = {"$not": {"$elemMatch": {"$nin": colors}}}

    if card_type:
        query["type_line"] = {"$regex": card_type.strip(), "$options": "i"}

    if max_mana_cost is not None:
        query["cmc"] = {"$lte": float(max_mana_cost)}  

    return query


def query_from_deck(deck_id):
    if not deck_id:
        return {"lang": "en"}

    deck = get_decks_collection().find_one({"_id": deck_id})
    if not deck:
        return {"lang": "en"}

    return query_from_filters(
        format=deck.get("format"),
        colors=deck.get("colors") or None,
    )

def _get_rocky_client():
    api_key = os.getenv("RoKEY")  # key go here
    if not api_key:
        raise RuntimeError("ROCKY_API_KEY is not set in your .env file.")
    headers = {"Authorization": f"Bearer {api_key}"}
    model = get_model(headers)
    return model, headers


def get_recommendations(question, format=None, colors=None, card_type=None, max_mana_cost=None, deck_id=None): 
    model, headers = _get_rocky_client()

    query = query_from_deck(deck_id) if deck_id else query_from_filters(format=format, colors=colors, card_type=card_type, max_mana_cost=max_mana_cost)
    cards = _fetch(query)
    return ask_rocky(question, cards, model, headers)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ask Rocky for card recommendations.")
    parser.add_argument("--format",       default="modern",  dest="format") 
    parser.add_argument("--colors",       default="",        help="Comma-separated, e.g. R,G")
    parser.add_argument("--type",         default="",        dest="card_type")
    parser.add_argument("--max-mana-cost", default=None,     type=float)  
    parser.add_argument("--deck-id",      default=None)
    args = parser.parse_args()

    colors = [c.strip().upper() for c in args.colors.split(",") if c.strip()]

    model, headers = _get_rocky_client()

    query = (
        query_from_deck(args.deck_id) if args.deck_id
        else query_from_filters(
            format=args.format,  
            colors=colors or None,
            card_type=args.card_type or None,
            max_mana_cost=args.max_mana_cost, 
        )
    )
    cards = _fetch(query)

    print(f"Loaded {len(cards)} cards.")

    while True:
        question = input("You: ").strip()
        try:
            answer = ask_rocky(question, cards, model, headers)
            print(f"\nRocky: {answer}\n")
