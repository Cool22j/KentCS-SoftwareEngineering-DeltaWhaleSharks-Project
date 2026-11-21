"""Tags for cards the logged-in user owns (issue #18).

Pages call load_owned_counts() once per run, then owned_badge() next to each card.
Matching is by card name, so any printing in the collection counts.
"""

import pymongo
import streamlit as st

import user_database as udb


def load_owned_counts():
    """Return {lowercase card name: copies owned} for the logged-in user, or {} if logged out."""
    user_id = st.session_state.get("user_id")
    if not user_id:
        return {}
    try:
        counts = udb.get_owned_counts(user_id)
    except (pymongo.errors.PyMongoError, RuntimeError):
        return {}
    return {name.lower(): qty for name, qty in counts.items() if name}


def owned_qty(counts, name):
    return counts.get((name or "").lower(), 0)


def owned_badge(counts, name, needed=None):
    """Show a small tag if the user owns the card.

    With `needed` (copies in a deck) it also says when the user is short, e.g. "Own 2 of 4".
    Shows nothing for cards the user doesn't own.
    """
    have = owned_qty(counts, name)
    if not have:
        return
    if needed is None or have >= needed:
        st.badge(f"Owned ×{have}", icon=":material/check_circle:", color="green")
    else:
        st.badge(f"Own {have} of {needed}", icon=":material/error:", color="orange")


def deck_owned_summary(counts, cards):
    """(copies of this deck the user already owns, total copies in the deck)."""
    total = sum(card.get("qty", 0) for card in cards)
    owned = sum(min(card.get("qty", 0), owned_qty(counts, card.get("name"))) for card in cards)
    return owned, total
