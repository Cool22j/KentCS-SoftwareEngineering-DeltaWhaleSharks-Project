

import os
import uuid
from datetime import datetime

import pymongo
import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # reads MONGODB_URI from the .env file


@st.cache_resource
def get_decks_collection():
    """Connect to MongoDB once and return the 'decks' collection."""
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise RuntimeError("MONGODB_URI is not set. Add it to your .env file.")
    client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
    return client["Magic_Cards"]["decks"]


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
