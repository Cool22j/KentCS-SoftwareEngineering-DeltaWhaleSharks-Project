import streamlit as st


#declare pages
deckBuilder = st.Page(
    "app.py",
    title = "Deck Builder",
    icon = ":material/build:",
    default = True
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

#create navigation bar
nv = st.navigation(
    [rules, deckBuilder, deckInventory],
    position = "top"
)
nv.run()

