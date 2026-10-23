"""
ROCKY_API_KEY #RocKEY
get_cards_collection()
get_decks_collection()
get_model()
ask_rocky()

get_recommendations() 

import json
import os
import requests

from dotenv import load_dotenv
from database import get_cards_collection, get_decks_collection
from rocky import get_model, ask_rocky

from langchain.schema import Document #wrapper            

load_dotenv()

#for formatting card data to text for rocky.py

#scryfall categories (like get_card_data.py)
CARD_FIELDS = (
    "id", "name", "mana_cost", "cmc", "type_line", "oracle_text",
    "colors", "color_identity", "power", "toughness", "loyalty",
    "legalities", "card_faces", "image_uris", "prices",
)
CARD_LIMIT = 80

#mongo
def _base_projection():
    proj = {field: 1 for field in CARD_FIELDS}
    proj["_id"] = 0
    return proj

# lang chain doc for it to read
def _cards_to_documents(cards):
    docs = []
    for card in cards:
        content = (
            f"Name: {card.get('name', 'Unknown')}\n"
            f"Mana Cost: {card.get('mana_cost', 'N/A')}  CMC: {card.get('cmc', '?')}\n"
            f"Type: {card.get('type_line', 'N/A')}\n"
            f"Colors: {', '.join(card.get('color_identity', [])) or 'Colorless'}\n"
            f"Oracle Text: {card.get('oracle_text', 'N/A')}\n"
            f"Power/Toughness: {card.get('power', '-')}/{card.get('toughness', '-')}\n"
            f"Prices: {json.dumps(card.get('prices', {}))}"
        )
        docs.append(Document(
            page_content=content,
            metadata={
                "scryfall_id": card.get("id", ""),
                "name":        card.get("name", ""),
                "cmc":         card.get("cmc", 0),
                "type_line":   card.get("type_line", ""),
                "colors":      card.get("color_identity", []),
                "prices":      card.get("prices", {}),
            }
        ))
    return docs

#for converting to rocky readable
def _docs_to_rocky_cards(docs):
    return [
        {"page_content": doc.page_content, **doc.metadata}
        for doc in docs
    ]

# mongo query + no case
def _fetch(query, limit=CARD_LIMIT):
    cards = list(
        get_cards_collection()
        .find(query, _base_projection())
        .sort("name", 1)
        .limit(limit)
    )
    if not cards:
        raise ValueError("No matching cards to this description. Please try loosening filters.")
    return cards

#mongo w/ user input (for cards)
def query_from_filters(format=None, colors=None, card_type=None, max_mana_cost=None):
    query = {"lang": "en"}
    known_formats = {
        "commander", "legacy", "modern",
        "pauper", "pioneer", "standard", "vintage",
    }
    if format and format.lower() in known_formats:
        query[f"legalities.{format.lower()}"] = "legal"

    if colors:
        query["color_identity"] = {"$not": {"$elemMatch": {"$nin": colors}}} #not not in

    if card_type:
        query["type_line"] = {"$regex": card_type.strip(), "$options": "i"}

    if max_mana_cost is not None:
        query["cmc"] = {"$lte": int(max_mana_cost)}

    return query

#mongo w/ user input (for decks)
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
    api_key = os.getenv("ROCKY_API_KEY")
    if not api_key:
        raise RuntimeError("ROCKY_API_KEY is not set in your .env file.")
    headers = {"Authorization": f"Bearer {api_key}"}
    model = get_model(headers)
    return model, headers

# filtered fetched wrapped converted then handed to rocky
def get_recommendations(question, format=None, colors=None, card_type=None, max_mana_cost=None, deck_id=None):
    model, headers = _get_rocky_client()
    query = (
        query_from_deck(deck_id) if deck_id
        else query_from_filters(
            format=format, colors=colors,
            card_type=card_type, max_mana_cost=max_mana_cost,
        )
    )
    cards = _fetch(query)
    docs = _cards_to_documents(cards)
    rocky_cards = _docs_to_rocky_cards(docs)
    return ask_rocky(question, rocky_cards, model, headers)

#main
if __name__ == "__main__":
    import argparse
    # manual in testing
    parser = argparse.ArgumentParser(description="Ask Rocky for card recommendations.")
    parser.add_argument("--format",        default="modern", dest="format")
    parser.add_argument("--colors",        default="",       help="Comma-separated e.g. R,G")
    parser.add_argument("--type",          default="",       dest="card_type")
    parser.add_argument("--max-mana-cost", default=None,     type=float)
    parser.add_argument("--deck-id",       default=None)
    args = parser.parse_args()

    colors = [c.strip().upper() for c in args.colors.split(",") if c.strip()]
    while True:
        question = input("You: ").strip()
        if not question:
            continue
        if question.lower() in ("exit", "quit", "q", "leave"): #from rocky.py
            print("Rocky: See you next time!")
            break
        try:
            answer = get_recommendations(
                question=question,
                format=args.format,
                colors=colors or None,
                card_type=args.card_type or None,
                max_mana_cost=args.max_mana_cost,
                deck_id=args.deck_id,
            )
            print(f"\nRocky: {answer}\n")
        except requests.RequestException as err:
            print(f"\nError talking to Rocky: {err}\n")
        except ValueError as err:
            print(f"\nFilter error: {err}\n")
"""
