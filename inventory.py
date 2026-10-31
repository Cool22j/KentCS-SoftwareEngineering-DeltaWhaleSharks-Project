import streamlit as st
import pymongo
import user_database as udb
from pages import edit

st.markdown(
    "<h1 style='text-align: center;'>Your Decks</h1>",
    unsafe_allow_html=True,
)

user_id = st.session_state.get("user_id")

if not user_id:
    st.info("Log in to see your saved decks.")
    st.page_link("login.py", label="Log In / Register", icon=":material/person:")
    st.stop()

try:
    decks = udb.get_decks(user_id)
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
                display = [
                    {
                        "Name": card["name"],
                        "Quantity": card["qty"],
                        "Role": card.get("role", "")
                    }
                    for card in deck["cards"]
                ]

                st.table(display)

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