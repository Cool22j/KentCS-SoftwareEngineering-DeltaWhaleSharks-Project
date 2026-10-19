import streamlit as st
import pymongo

import database as db
st.markdown(
    "<h1 style='text-align: center;'>Your Decks:</h1>",
    unsafe_allow_html=True
)
st.header("Your Decks:")

try:
    #sample data for demonstration purposes:
    decks = [
        {"_id": "001", "name": "myDeck1", "format": "standard", "colors": "green, white", "strategy": "aggressive", "created_at": "10/19/26",  "cards": []},
        {"_id": "002", "name": "myDeck2", "format": "commander", "colors": "red", "strategy": "aggressive", "created_at": "10/12/26",  "cards": []},
        {"_id": "003", "name": "myDeck3", "format": "commander", "colors": "black, blue", "strategy": "defensive", "created_at": "10/12/26",  "cards": []},
        {"_id": "004", "name": "myDeck4", "format": "standard", "colors": "red", "strategy": "defensive", "created_at": "10/14/26",  "cards": []},
        {"_id": "005", "name": "myDeck5", "format": "standard", "colors": "blue", "strategy": "defensive", "created_at": "10/16/26",  "cards": []},

    ]
    #the code to use the actual data 
    #decks = db.get_decks(st.session_state.get("user_id"))
except (pymongo.errors.PyMongoError, RuntimeError) as error:
    st.error(f"Could not load decks: {error}")
    st.stop()

if not decks:
    st.info("No saved decks yet. Build one on the Deck Builder page!")

col1, col2 = st.columns(2)

st.markdown("""
<style>
div[data-testid="stExpander"] {
    border-radius: 16px;
    width: 300px;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)
for i, deck in enumerate(decks):
    column = col1 if i % 2 == 0 else col2
    with column: 
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
