import streamlit as st
import pymongo
import database as db

st.markdown(
    "<h1 style='text-align: center;'>Your Decks</h1>",
    unsafe_allow_html=True,
)

try:
    decks = db.get_decks(st.session_state.get("user_id"))
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
