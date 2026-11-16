import streamlit as st

# declare pages
landing = st.Page(
    "pages/landing.py",
    title="Home",
    icon=":material/home:",
    default=True,
)

deckBuilder = st.Page(
    "pages/app.py",
    title="Deck Builder",
    icon=":material/build:",
)

deckInventory = st.Page(
    "pages/inventory.py",
    title="Deck Inventory",
    icon=":material/favorite:",
)

rules = st.Page(
    "pages/rules.py",
    title="Rules",
    icon=":material/menu_book:",
)

beginner = st.Page(
    "pages/beginner.py",
    title="Beginner's Guide",
    icon=":material/school:",
)

cardCollection = st.Page(
    "pages/collection.py",
    title="My Collection",
    icon=":material/collections_bookmark:",
)

account = st.Page(
    "pages/login.py",
    title="Account",
    icon=":material/person:",
)

edit = st.Page(
    "pages/edit_deck.py",
    visibility="hidden",
)

__all__ = [
    "landing",
    "deckBuilder",
    "deckInventory",
    "rules",
    "beginner",
    "cardCollection",
    "account",
    "edit",
]
