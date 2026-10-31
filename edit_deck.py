import streamlit as st
import pymongo
import database as db
import user_database as udb
from pages import deckInventory


deck = st.session_state.get("deckToEdit")
st.markdown(
    f"<h1 style='text-align: center;'> {deck['name']} </h1>",
    unsafe_allow_html=True,
)
st.write("Format:", deck["format"])
st.write("Colors:", deck["colors"])

with st.container(border=True): 
    st.write("Strategy:", deck["strategy"])


st.subheader("Cards:")

outCol1, outCol2 = st.columns([1, 1])

for i, card in enumerate(deck["cards"]):
    if i%2 == 0:
        with outCol1:
            with st.container(border=True, height = 280, width = 300):

                col1, col2, col3 = st.columns([1, 3, 1])

                with col1:
                    if st.button("−", key=f"remove_{i}"):
                        if card["qty"] > 1:
                            card["qty"] -= 1
                        else:
                            deck["cards"].remove(card)

                        st.rerun()

                with col2:
                    image_url = (card.get("image_uris") or {}).get("normal")
                    if not image_url:
                        faces = card.get("card_faces") or []
                        if faces:
                            image_url = (
                                (faces[0].get("image_uris") or {}).get("normal")
                            )          
                    if image_url:
                        st.image(image_url, use_container_width=True)
                    else:
                        st.caption("Image unavailable")
                    st.caption(f"X: {card['qty']}")

                with col3:
                    if st.button("+", key=f"add_{i}"):
                        card["qty"] += 1
                        st.rerun()
    else:
        with outCol2:
            with st.container(border=True, height = 280, width = 300):

                col1, col2, col3 = st.columns([1, 3, 1])

                with col1:
                    if st.button("−", key=f"remove_{i}"):
                        if card["qty"] > 1:
                            card["qty"] -= 1
                        else:
                            deck["cards"].remove(card)

                        st.rerun()

                with col2:
                    image_url = (card.get("image_uris") or {}).get("normal")
                    if not image_url:
                        faces = card.get("card_faces") or []
                        if faces:
                            image_url = (
                                (faces[0].get("image_uris") or {}).get("normal")
                            )          
                    if image_url:
                        st.image(image_url, use_container_width=True)
                    else:
                        st.caption("Image unavailable")
                    st.caption(f"X: {card['qty']}")

                with col3:
                    if st.button("+", key=f"add_{i}"):
                        card["qty"] += 1
                        st.rerun()


cards = deck["cards"]
user_id = deck["user_id"]

if st.button("Cancel", disabled=not user_id):
    st.switch_page(deckInventory)

if st.button("Save Deck", disabled=not user_id):
    try:
        updated = deck.get("_id") and udb.update_deck(
            deck["_id"],
            user_id,
            name=deck["name"],
            deck_format=deck["format"],
            colors=deck["colors"],
            strategy=deck["strategy"],
            deck_cards=cards,
        )
        if updated:
            st.success("Deck updated!")
        else:
            deck["_id"] = udb.save_deck(
                name=deck["name"],
                deck_format=deck["format"],
                colors=deck["colors"],
                strategy=deck["strategy"],
                deck_cards=cards,
                user_id=user_id,
            )
            st.success("Deck saved successfully!")
    except (pymongo.errors.PyMongoError, RuntimeError, ValueError) as error:
        st.error(f"Could not save deck: {error}")