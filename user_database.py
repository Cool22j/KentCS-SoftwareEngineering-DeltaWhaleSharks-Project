"""Database code for users and for decks owned by users.

database.py keeps the connection and the card catalog; this file adds the
users collection and the owner-scoped deck operations on top of it.
"""

import uuid
from datetime import datetime
from functools import lru_cache

import database as db

# Users collection

@lru_cache(maxsize=1)
def _create_users_indexes():
    """Create the unique indexes on the users collection (once per process)."""
    users = db.get_database()["users"]
    users.create_index("email", unique=True)
    users.create_index("username", unique=True)
    return True


def get_users_collection():
    """Return the users collection, creating it and its unique indexes if needed."""
    _create_users_indexes()
    return db.get_database()["users"]


# Decks owned by a user

@lru_cache(maxsize=1)
def _create_decks_indexes():
    """Index decks by owner and date so each user's list loads fast (once per process)."""
    db.get_decks_collection().create_index([("user_id", 1), ("created_at", -1)])
    return True


def get_user_decks_collection():
    """Return the decks collection with the owner index in place."""
    _create_decks_indexes()
    return db.get_decks_collection()


def save_deck(name, deck_format, colors, strategy, deck_cards, user_id):
    """Save a new deck for a user and return its id."""
    if not user_id:
        raise ValueError("You must be logged in to save a deck.")
    deck_id = uuid.uuid4().hex
    get_user_decks_collection().insert_one({
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


def update_deck(deck_id, user_id, name, deck_format, colors, strategy, deck_cards):
    """Overwrite a deck, only if it belongs to the user. Returns True if it was found."""
    if not user_id:
        return False
    result = get_user_decks_collection().update_one(
        {"_id": deck_id, "user_id": user_id},
        {"$set": {
            "name": name,
            "format": deck_format,
            "colors": colors,
            "strategy": strategy,
            "cards": list(deck_cards),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }},
    )
    return result.matched_count > 0


def get_decks(user_id):
    """Return the user's saved decks, newest first. No user means no decks."""
    if not user_id:
        return []
    return list(get_user_decks_collection().find({"user_id": user_id}).sort("created_at", -1))


def delete_deck(deck_id, user_id):
    """Delete a deck only if it belongs to the user. Returns True if it was deleted."""
    if not user_id:
        return False
    result = get_user_decks_collection().delete_one({"_id": deck_id, "user_id": user_id})
    return result.deleted_count > 0