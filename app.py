import streamlit as st
import pymongo

import database as db

#include rocky


st.title("MTG Deck Builder")

st.write("Create a Magic: The Gathering deck using Rocky.")


deck_name = st.text_input("Deck Name")

colors = st.text_input("Colors")

deck_format = st.selectbox(
    "Format",
    ["Standard", "Modern", "Commander", "Pioneer", "Legacy", "Vintage"]
)

strategy = st.text_area(
    "What kind of deck do you want?",
    placeholder="Example: Aggressive artifact deck with lots of card draw"
)

if st.button("Generate Deck"):
    if not colors:
        st.warning("Please enter deck colors")
    elif not strategy:
        st.warning("Please enter a deck strategy")
    else:
        with st.spinner("Generating deck..."):
            st.session_state["deck"] = {
                "name": deck_name or "Untitled Deck",
                "colors": colors,
                "format": deck_format,
                "strategy": strategy,
                "cards": [],  # TODO: generate actual cards
            }

if "deck" in st.session_state:
    st.subheader("Generated Deck")
    st.write(st.session_state["deck"])

    if st.button("Save Deck"):
        try:
            deck = st.session_state["deck"]
            db.save_deck(
                name=deck["name"],
                deck_format=deck["format"],
                colors=deck["colors"],
                strategy=deck["strategy"],
                deck_cards=deck.get("cards", []),
                user_id=st.session_state.get("user_id"),
            )
        except (pymongo.errors.PyMongoError, RuntimeError) as error:
            st.error(f"Could not save deck to MongoDB: {error}")
        else:
            st.success("Deck saved!")