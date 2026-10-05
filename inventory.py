import streamlit as st
import pymongo

import database as db

st.title("Your Decks:")

try:
    decks = db.get_decks(st.session_state.get("user_id"))
except (pymongo.errors.PyMongoError, RuntimeError) as error:
    st.error(f"Could not load decks: {error}")
    st.stop()

if not decks:
    st.info("No saved decks yet. Build one on the Deck Builder page!")

for deck in decks:
    card_count = sum(card["qty"] for card in deck["cards"])
    with st.expander(f"{deck['name']}  ·  {deck['format']}  ·  {card_count} cards"):
        st.write(f"**Colors:** {deck['colors']}")
        st.write(f"**Strategy:** {deck['strategy']}")
        st.write(f"**Saved:** {deck['created_at']}")

        if deck["cards"]:
            st.table(deck["cards"])
        else:
            st.caption("This deck has no cards yet.")

        if st.button("Delete deck", key=f"delete_{deck['_id']}"):
            db.delete_deck(deck["_id"])
            st.rerun()
