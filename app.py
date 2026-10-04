import streamlit as st
import os
import pymongo

#include rocky


MONGODB_URI = os.getenv("MONGODB_URI")
mongo_client = pymongo.MongoClient(MONGODB_URI) if MONGODB_URI else None
mongo_database = (
    mongo_client["Magic_Cards"] if mongo_client is not None else None
)
mongo_collection = (
    mongo_database["Magic_Card_Collection"]
    if mongo_database is not None
    else None
)


def save_deck_to_mongodb(deck):
    """Save a generated deck when a MongoDB URI is configured."""
    if mongo_collection is None:
        raise RuntimeError("MONGODB_URI is not configured")
    return mongo_collection.insert_one(deck)


st.title("MTG Deck Builder")

st.write("Create a Magic: The Gathering deck using Rocky.")


colors = st.text_input("Colors")

format = st.selectbox(
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
                "colors": colors,
                "format": format,
                "strategy": strategy,
            }

if "deck" in st.session_state:
    st.subheader("Generated Deck")
    st.write(st.session_state["deck"])

    if st.button("Save Deck"):
        try:
            save_deck_to_mongodb(st.session_state["deck"])
        except (pymongo.errors.PyMongoError, RuntimeError) as error:
            st.error(f"Could not save deck to MongoDB: {error}")
        else:
            st.success("Deck saved!")