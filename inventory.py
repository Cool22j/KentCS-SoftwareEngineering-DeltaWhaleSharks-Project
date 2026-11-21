
import html
import re

import streamlit as st
import pymongo

import database as db
import user_database as udb
from pages import edit
from search import get_card_image_url
from owned import load_owned_counts, owned_badge, owned_qty, deck_owned_summary

PREVIEW_CARDS = 3
GRID_COLUMNS = 5

st.markdown(
    "<h1 style='text-align: center;'>Your Decks</h1>",
    unsafe_allow_html=True,
)

user_id = st.session_state.get("user_id")

if not user_id:
    st.info("Log in to see your saved decks.")
    st.page_link("login.py", label="Log In / Register", icon=":material/person:")
    st.stop()


@st.cache_data(ttl=3600, show_spinner=False)
def lookup_image_url(name):
    """Find an image in the card catalog for cards saved without one (e.g. typed in by hand)."""
    try:
        card = db.get_cards_collection().find_one(
            {
                "name": {"$regex": f"^{re.escape(name)}$", "$options": "i"},
                "lang": "en",
                "$or": [
                    {"image_uris": {"$exists": True}},
                    {"card_faces.image_uris": {"$exists": True}},
                ],
            },
            {"image_uris": 1, "card_faces": 1},
        )
    except (pymongo.errors.PyMongoError, RuntimeError):
        return None
    return get_card_image_url(card) if card else None


def image_for(card):
    return get_card_image_url(card) or (lookup_image_url(card["name"]) if card.get("name") else None)


def show_card_tile(card, owned_counts):
    """One card in the grid: the image, or a placeholder box with the name if there is none."""
    image_url = image_for(card)
    if image_url:
        st.image(image_url, width="stretch")
    else:
        st.markdown(
            f"""
            <div style="aspect-ratio: 63 / 88; border: 1px solid rgba(250,250,250,0.2);
                        border-radius: 10px; display: flex; align-items: center;
                        justify-content: center; text-align: center; padding: 8px;">
                {html.escape(card.get("name", "Unknown"))}
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown(f"**{card['qty']}×** {card.get('name', 'Unknown')}")
    if card.get("role"):
        st.caption(str(card["role"]).capitalize())
    owned_badge(owned_counts, card.get("name"), needed=card["qty"])


@st.dialog("Deck list", width="large")
def show_deck_cards(deck):
    cards = deck["cards"]
    total = sum(card["qty"] for card in cards)
    st.subheader(deck["name"])
    st.caption(f"{deck['format']}  ·  {total} cards  ·  {len(cards)} unique")
    owned_counts = load_owned_counts()

    view = st.segmented_control(
        "View",
        ["Cards", "List"],
        default="Cards",
        key=f"view_{deck['_id']}",
        label_visibility="collapsed",
    )

    if view == "List":
        st.table([
            {
                "Name": card["name"],
                "Quantity": card["qty"],
                "Owned": owned_qty(owned_counts, card["name"]),
                "Role": card.get("role", ""),
            }
            for card in cards
        ])
        return

    for start in range(0, len(cards), GRID_COLUMNS):
        row = st.columns(GRID_COLUMNS)
        for column, card in zip(row, cards[start:start + GRID_COLUMNS]):
            with column:
                show_card_tile(card, owned_counts)


try:
    decks = udb.get_decks(user_id)
except (pymongo.errors.PyMongoError, RuntimeError) as error:
    st.error(f"Could not load decks: {error}")
    st.stop()

if not decks:
    st.info("No saved decks yet. Build one on the Deck Builder page!")

owned_counts = load_owned_counts()
deck_columns = st.columns(3)

for i, deck in enumerate(decks):
    with deck_columns[i % 3]:
        card_count = sum(card["qty"] for card in deck["cards"])

        with st.container(border=True):
            st.header(deck["name"])
            st.write(f"{deck['format']}  ·  {card_count} cards")
            if owned_counts:
                owned_copies, _ = deck_owned_summary(owned_counts, deck["cards"])
                st.caption(f"You own {owned_copies} of {card_count} cards")

            # Preview: the first few cards that have a picture
            preview_urls = []
            for card in deck["cards"]:
                url = image_for(card)
                if url:
                    preview_urls.append(url)
                if len(preview_urls) == PREVIEW_CARDS:
                    break

            with st.container(border=True):
                st.caption("Preview")
                if preview_urls:
                    for column, url in zip(st.columns(PREVIEW_CARDS), preview_urls):
                        with column:
                            st.image(url, width="stretch")
                else:
                    st.caption("No card images available")

            st.write(f"**Colors:** {deck['colors']}")

            st.markdown(
                f"""
                <div style="
                display: -webkit-box;
                -webkit-line-clamp: 3;
                -webkit-box-orient: vertical;
                overflow: hidden;
                text-overflow: ellipsis;
                ">
                    {html.escape(str(deck["strategy"]))}
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.write(f"**Saved:** {deck['created_at']}")

            if deck["cards"]:
                if st.button("See all cards", key=f"cards_{deck['_id']}", width="stretch"):
                    show_deck_cards(deck)
            else:
                st.caption("This deck has no cards yet.")

            buttonCol1, buttonCol2 = st.columns(2)
            with buttonCol1:
                if st.button("Delete deck", key=f"delete_{deck['_id']}"):
                    try:
                        udb.delete_deck(deck["_id"], user_id)
                    except (pymongo.errors.PyMongoError, RuntimeError) as error:
                        st.error(f"Could not delete deck: {error}")
                    else:
                        st.rerun()
            with buttonCol2:
                if st.button("Edit deck", key=f"edit_{deck['_id']}"):
                    st.session_state["deckToEdit"] = deck
                    st.switch_page(edit)