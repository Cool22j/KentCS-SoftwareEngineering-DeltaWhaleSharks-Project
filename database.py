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