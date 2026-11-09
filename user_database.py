"""Database code for users and for decks owned by users.

database.py keeps the connection and the card catalog; this file adds the
users collection and the owner-scoped deck operations on top of it.
"""

import uuid
from datetime import datetime, timezone
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


# Cards a user owns (their collection)
#
# One document per user per printing, so owning 3 Lightning Bolts from two
# different sets is two documents. The unique index stops duplicate rows when
# two adds happen at the same time.

@lru_cache(maxsize=1)
def _create_owned_cards_indexes():
    """Create the indexes on the owned_cards collection (once per process)."""
    owned = db.get_database()["owned_cards"]
    owned.create_index([("user_id", 1), ("card_id", 1)], unique=True)
    owned.create_index([("user_id", 1), ("name", 1)])
    return True


def get_owned_cards_collection():
    """Return the owned_cards collection with its indexes in place."""
    _create_owned_cards_indexes()
    return db.get_database()["owned_cards"]


def _card_image_url(card):
    """Pick an image for a card, falling back to the front face of double-faced cards."""
    image_uris = card.get("image_uris") or {}
    if image_uris.get("normal"):
        return image_uris["normal"]
    faces = card.get("card_faces") or []
    if faces and isinstance(faces[0], dict):
        return (faces[0].get("image_uris") or {}).get("normal")
    return None


def _card_price(card):
    """Return the Scryfall USD price as a float, or None if it has no price."""
    try:
        return float((card.get("prices") or {}).get("usd"))
    except (TypeError, ValueError):
        return None


def add_to_collection(user_id, card, qty=1):
    """Add copies of a card printing to the user's collection."""
    if not user_id:
        raise ValueError("You must be logged in to add cards to your collection.")
    if not isinstance(qty, int) or not 1 <= qty <= 999:
        raise ValueError("Quantity must be a whole number between 1 and 999.")
    if not card or not card.get("id"):
        raise ValueError("That card could not be found.")

    now = datetime.now(timezone.utc)
    get_owned_cards_collection().update_one(
        {"user_id": user_id, "card_id": card["id"]},
        {
            "$inc": {"qty": qty},
            "$set": {"updated_at": now},
            "$setOnInsert": {
                "name": card.get("name", ""),
                "set": card.get("set", ""),
                "set_name": card.get("set_name", ""),
                "collector_number": card.get("collector_number", ""),
                "type_line": card.get("type_line", ""),
                "color_identity": card.get("color_identity", []),
                "rarity": card.get("rarity", ""),
                "image_url": _card_image_url(card),
                "price_usd": _card_price(card),
                "added_at": now,
            },
        },
        upsert=True,
    )


def set_owned_qty(user_id, card_id, qty):
    """Set how many copies the user owns. 0 or less removes the card. Returns True if found."""
    if not user_id:
        return False
    owned = get_owned_cards_collection()
    if qty <= 0:
        return owned.delete_one({"user_id": user_id, "card_id": card_id}).deleted_count > 0
    result = owned.update_one(
        {"user_id": user_id, "card_id": card_id},
        {"$set": {"qty": int(qty), "updated_at": datetime.now(timezone.utc)}},
    )
    return result.matched_count > 0


def remove_from_collection(user_id, card_id):
    """Remove a card printing from the user's collection. Returns True if it was there."""
    return set_owned_qty(user_id, card_id, 0)


def get_collection(user_id):
    """Return every card the user owns, sorted by name. No user means no cards."""
    if not user_id:
        return []
    return list(get_owned_cards_collection().find({"user_id": user_id}).sort([("name", 1), ("set", 1)]))


def get_owned_counts(user_id):
    """Return {card name: total copies owned across all printings} for the user."""
    if not user_id:
        return {}
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": "$name", "qty": {"$sum": "$qty"}}},
    ]
    return {row["_id"]: row["qty"] for row in get_owned_cards_collection().aggregate(pipeline)}
