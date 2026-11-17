
import streamlit as st
import pymongo
import user_database as udb
from pages import edit
from search import get_card_image_url


st.markdown(
    "<h1 style='text-align: center;'>Your Decks</h1>",
    unsafe_allow_html=True,
)

user_id = st.session_state.get("user_id")

if not user_id:
    st.info("Log in to see your saved decks.")
    st.page_link(
        "login.py",
        label="Log In / Register",
        icon=":material/person:",
    )
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
div[data-testid="stExpander"]:not(:has(div[data-testid="stExpander"])) {
    border-radius: 16px;
    width: 300px;
    max-width: 100%;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

for i, deck in enumerate(decks):
    column = col1 if i % 2 == 0 else col2

    with column:

        cards = deck.get("cards", [])
        card_count = sum(card["qty"] for card in cards)

        with st.expander(
            f"{deck['name']}  ·  {deck['format']}  ·  {card_count} cards"
        ):

            # Show deck preview
            with st.container(border=True):
                st.caption("Preview")

                image_url = (
                    get_card_image_url(cards[0])
                    if cards else None
                )

                if image_url:
                    st.image(image_url, width=150)
                else:
                    st.caption("Image unavailable")

            st.write(f"**Colors:** {deck['colors']}")
            st.write(f"**Strategy:** {deck['strategy']}")
            st.write(f"**Saved:** {deck['created_at']}")

            # Display all cards visually
            if cards:

                with st.expander(
                    label="See All Cards",
                    expanded=False,
                    width="stretch",
                ):

                    st.caption(f"Total Cards: {card_count}")
                    st.caption(f"Unique Cards: {len(cards)}")

                    # Create two columns for card images
                    card_columns = st.columns(2)

                    for j, card in enumerate(cards):

                        with card_columns[j % 2]:

                            with st.container(border=True):

                                card_image = get_card_image_url(card)

                                # Display card image
                                if card_image:
                                    st.image(
                                        card_image,
                                        use_container_width=True,
                                    )
                                else:
                                    st.caption("Image unavailable")

                                # Display card name
                                st.write(
                                    card.get("name", "Unknown Card")
                                )

                                # Display card quantity
                                st.caption(
                                    f"Quantity: {card.get('qty', 1)}"
                                )

                                # Display card role if available
                                role = card.get("role")

                                if role:
                                    st.caption(f"Role: {role}")

            else:
                st.caption("This deck has no cards yet.")

            # Existing edit and delete functionality
            buttonCol1, buttonCol2 = st.columns(2)

            with buttonCol1:

                if st.button(
                    "Delete deck",
                    key=f"delete_{deck['_id']}",
                ):

                    try:
                        udb.delete_deck(deck["_id"], user_id)

                    except (
                        pymongo.errors.PyMongoError,
                        RuntimeError,
                    ) as error:

                        st.error(f"Could not delete deck: {error}")

                    else:
                        st.rerun()

            with buttonCol2:

                if st.button(
                    "Edit deck",
                    key=f"edit_{deck['_id']}",
                ):

                    st.session_state["deckToEdit"] = deck
                    st.switch_page(edit)
