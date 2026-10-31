import streamlit as st

#declare pages
landing = st.Page(
    "landing.py",
    title = "Home",
    icon = ":material/home:",
    default = True
)

deckBuilder = st.Page(
    "app.py",
    title = "Deck Builder",
    icon = ":material/build:",
)

deckInventory = st.Page(
    "inventory.py",
    title = "Deck Inventory",
    icon = ":material/favorite:"
)

rules = st.Page(
    "rules.py",
    title = "Rules",
    icon = ":material/menu_book:"
)

beginner = st.Page(
    "beginner.py",
    title = "Beginner's Guide",
    icon = ":material/school:"
)

account = st.Page(
    "login.py",
    title = "Account",
    icon = ":material/person:"
)

edit = st.Page(
    "edit_deck.py",
    visibility = "hidden"
)