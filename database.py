

import os
import re
import uuid
from datetime import datetime
from functools import lru_cache

import pymongo
from dotenv import load_dotenv

load_dotenv()  # reads MONGODB_URI from the .env file


@lru_cache(maxsize=1)
def get_database():
    """Share one MongoDB connection across cards and decks."""
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise RuntimeError("MONGODB_URI is not set. Add it to your .env file.")
    client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
    return client["Magic_Cards"]


def get_decks_collection():
    """Return saved decks, separate from the imported card catalog."""
    return get_database()["decks"]


def get_cards_collection():
    """Return the imported Scryfall card catalog."""
    return get_database()["Cards"]


def search_cards(name="", limit=20, card_type=""):
    """Find English printings by part of their name or type, alphabetically."""
    if not isinstance(limit, int) or not 1 <= limit <= 5000:
        raise ValueError("limit must be an integer between 1 and 5000")
    query = {"lang": "en"}
    if name.strip():
        query["name"] = {"$regex": re.escape(name.strip()), "$options": "i"}
    if card_type.strip():
        query["type_line"] = {"$regex": re.escape(card_type.strip()), "$options": "i"}
    return list(get_cards_collection().find(query).sort("name", 1).limit(limit))


def save_deck(name, deck_format, colors, strategy, deck_cards, user_id=None):
    """Save a new deck and return its id."""
    deck_id = uuid.uuid4().hex
    get_decks_collection().insert_one({
        "_id": deck_id,
        "user_id": user_id,
        "name": name,
        "format": deck_format,
        "colors": colors,
        "strategy": strategy,
        "cards": list(deck_cards),
        "created_at": datetime.now().isoformat(timespec="seconds"),
    })
    return deck_id


def get_decks(user_id=None):
    """Return all saved decks, newest first."""
    query = {"user_id": user_id} if user_id else {}
    return list(get_decks_collection().find(query).sort("created_at", -1))


def delete_deck(deck_id):
    """Delete a deck. Returns True if it was deleted."""
    return get_decks_collection().delete_one({"_id": deck_id}).deleted_count > 0
