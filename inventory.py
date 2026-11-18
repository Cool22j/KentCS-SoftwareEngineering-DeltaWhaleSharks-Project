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

col1, col2, col3 = st.columns([1, 1, 1])

st.markdown("""
<style>
div[data-testid="stExpander"]:not(:has(div[data-testid="stExpander"])) {
    border-radius: 16px;
    width: 300px;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

for i, deck in enumerate(decks):
    if i%3 == 0:
        column = col1
    if i%3 == 1:
        column = col2
    if i%3 == 2:
        column = col3
    with column:
        card_count = sum(card["qty"] for card in deck["cards"])

        with st.container(border = True):
            st.header(f"{deck['name']}")
            st.write(f"{deck['format']}  ·  {card_count} cards")
            with st.container(border = True):
                st.caption("Preview")
                col1Img, col2Img, col3Img = st.columns([1, 1, 1])
                with col1Img:
                    image_url = (deck["cards"][0].get("image_uris") or {}).get("normal")
                    if not image_url:
                        faces = deck["cards"][0].get("card_faces") or []
                        if faces:
                            image_url = (
                                (faces[0].get("image_uris") or {}).get("normal")
                            )          
                    if image_url:
                        st.image(image_url, width = 150)
                    else:
                        st.caption("Image unavailable")
                        st.image(image_url, width = 150)
                with col2Img:
                    image_url = (deck["cards"][1].get("image_uris") or {}).get("normal")
                    if not image_url:
                        faces = deck["cards"][1].get("card_faces") or []
                        if faces:
                            image_url = (
                                (faces[0].get("image_uris") or {}).get("normal")
                            )          
                    if image_url:
                        st.image(image_url, width = 150)
                    else:
                        st.caption("Image unavailable")
                        #st.image(image_url, width = 150)
                with col3Img:
                    image_url = (deck["cards"][2].get("image_uris") or {}).get("normal")
                    if not image_url:
                        faces = deck["cards"][2].get("card_faces") or []
                        if faces:
                            image_url = (
                                (faces[0].get("image_uris") or {}).get("normal")
                            )          
                    if image_url:
                        st.image(image_url, width = 150)
                    else:
                        st.caption("Image unavailable")
                        st.image(image_url, width = 150)
            st.write(f"**Colors:** {deck['colors']}")
            strat = deck["strategy"]

            st.markdown(
                f"""
                <div style="
                display: -webkit-box;
                -webkit-line-clamp: 3;
                -webkit-box-orient: vertical;
                overflow: hidden;                    
                text-overflow: ellipsis;
                ">
                    {strat}
                </div>
                """,
                unsafe_allow_html=True
            )

            st.write(f"**Saved:** {deck['created_at']}")

            deck_cost = sum(float(card.get("usd_price", 0) or 0) * card.get("qty", 1) for card in deck["cards"])
            if deck_cost > 0:
                st.write(f"**Estimated Cost:** ${deck_cost:.2f} USD")

            if deck["cards"]:
                with st.expander(label = "See All Cards", expanded = False, width= "stretch"):
                    display = [
                        {
                            "Name": card["name"],
                            "Quantity": card["qty"],
                            "Role": card.get("role", ""),
                            "Price (USD)": f"${float(card.get('usd_price', 0) or 0):.2f}"
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
