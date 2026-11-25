import base64
from pathlib import Path
import streamlit as st
import pymongo
import requests
import user_database as udb
from recommendation import get_recommendations
from rocky import get_model as get_rocky_model
import database as db
from owned import load_owned_counts, owned_badge, deck_owned_summary

def get_card_image_url(card):
    #extract image URL from Scryfall API
    image_urls = card.get("image_uris") or card.get("image_urls")

    if isinstance(image_urls, dict):
        url = (
            image_urls.get("normal")
            or image_urls.get("small")
            or image_urls.get("large")
        )
        if url:
            return url

    faces = card.get("card_faces")

    if isinstance(faces, list) and len(faces) > 0:
        if isinstance(faces[0], dict):
            face_urls = faces[0].get("image_uris")

            if isinstance(face_urls, dict):
                url = (
                    face_urls.get("normal")
                    or face_urls.get("small")
                    or face_urls.get("large")
                )
                if url:
                    return url
    return None

def attach_card_image(card):
    # find and attach image info to card

    if card.get("image_uris") or card.get("image_urls") or card.get("card_faces"):
        return card

    results = db.search_cards(card["name"], limit=20)

    for result in results:
        if result.get("name", "").lower() == card["name"].lower():
            card["id"] = result.get("id")
            card["image_uris"] = result.get("image_uris")
            card["image_urls"] = result.get("image_uris")
            card["card_faces"] = result.get("card_faces")
            break
    return card


@st.cache_data
def _spinner_video_html():
    video_path = Path(__file__).parent / "0000-0018.mp4"
    video_data = base64.b64encode(video_path.read_bytes()).decode("utf-8")
    return (
        '<video autoplay loop muted playsinline '
        'style="width:96px; height:auto; margin-top:-20px; border-radius:8px; display:block;">'
        f'<source src="data:video/mp4;base64,{video_data}" type="video/mp4">'
        "</video>"
    )


st.title("MTG Deck Builder")

# Initialize Rocky model in session state
if "rocky_model" not in st.session_state:
    try:
        st.session_state["rocky_model"] = get_rocky_model()
    except (RuntimeError, requests.RequestException):
        st.session_state["rocky_model"] = None

# Initialize chat history and deck state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "deck" not in st.session_state:
    st.session_state["deck"] = None

# Compact deck settings bar
set_col1, set_col2, set_col3 = st.columns([2, 2, 1.5])
with set_col1:
    deck_name = st.text_input("Deck Name", placeholder="Untitled Deck")
with set_col2:
    colors = st.text_input(
        "Colors (optional)",
        placeholder="Dimir, blue-black, U B, or leave blank",
    )
with set_col3:
    deck_format = st.selectbox(
        "Format",
        ["Standard", "Modern", "Commander", "Pioneer", "Legacy", "Vintage", "Pauper"],
    )

# Accept user input (pinned at bottom like Gemini)
prompt = st.chat_input("Describe the deck you want, or how to adjust it...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

# Use a Gemini-style split layout (Chat on left, Deck Canvas on right) once a deck exists
if st.session_state["deck"] is not None or prompt:
    chat_col, deck_col = st.columns([1.05, 1.15], gap="large")
else:
    chat_col = st.container()
    deck_col = None

with chat_col:
    chat_box = st.container(height=600, border=False)
    with chat_box:
        if not st.session_state.messages:
            st.caption("Tell Rocky what kind of Magic deck you want to build, then keep chatting to refine it.")
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt:
            user_prompts = [m["content"] for m in st.session_state.messages if m["role"] == "user"]
            combined_strategy = user_prompts[0]
            if len(user_prompts) > 1:
                combined_strategy += ". Adjustments: " + "; ".join(user_prompts[1:])

            with st.chat_message("assistant"):
                loader = st.empty()
                loader.markdown(_spinner_video_html(), unsafe_allow_html=True)
                try:
                    result = get_recommendations(
                        combined_strategy,
                        format=deck_format,
                        colors=colors,
                    )
                    loader.empty()

                    st.session_state["deck"] = {
                        "name": deck_name.strip() or "Untitled Deck",
                        "colors": ", ".join(result["colors"]),
                        "format": deck_format,
                        "strategy": result["strategy"],
                        "cards": result["cards"],
                    }
                    response = result["strategy"]
                    st.markdown(response)
                except (ValueError, RuntimeError, requests.RequestException, pymongo.errors.PyMongoError) as error:
                    loader.empty()
                    response = f"Could not generate deck: {error}"
                    st.error(response)

            st.session_state.messages.append({"role": "assistant", "content": response})

# Deck Canvas panel on the right (no duplicate strategy/metadata repetition)
if deck_col is not None and st.session_state["deck"] is not None:
    deck = st.session_state["deck"]
    if deck_name.strip():
        deck["name"] = deck_name.strip()
    cards = deck["cards"]
    total_cards = sum(card["qty"] for card in cards)
    owned_counts = load_owned_counts()
    owned_copies, _ = deck_owned_summary(owned_counts, cards)
    user_id = st.session_state.get("user_id")

    with deck_col:
        with st.container(border=True):
            # Header row: deck title + quick actions
            hdr_left, hdr_right = st.columns([2.2, 1.8])
            with hdr_left:
                st.subheader(deck["name"])
                st.caption(
                    f"{deck['format']} · {deck['colors'] or 'Colorless'} · "
                    f"{total_cards} cards ({len(cards)} unique) · "
                    f"Owned {owned_copies}/{total_cards}"
                )
            with hdr_right:
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    save_clicked = st.button(
                        "Save",
                        type="primary",
                        use_container_width=True,
                        disabled=not user_id,
                    )
                with btn_col2:
                    st.download_button(
                        "Export",
                        "\n".join(f"{c['qty']} {c['name']}" for c in cards),
                        file_name=f"{deck['name'].lower().replace(' ', '_')}.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )

            if not user_id:
                st.page_link("login.py", label="Log in to save decks", icon=":material/person:")

            if save_clicked:
                if len(cards) == 0:
                    st.warning("Add some cards before saving")
                else:
                    try:
                        updated = deck.get("saved_id") and udb.update_deck(
                            deck["saved_id"],
                            user_id,
                            name=deck["name"],
                            deck_format=deck["format"],
                            colors=deck["colors"],
                            strategy=deck["strategy"],
                            deck_cards=cards,
                            tags=deck.get("tags", []),
                        )
                        if updated:
                            st.success("Deck updated!")
                        else:
                            deck["saved_id"] = udb.save_deck(
                                name=deck["name"],
                                deck_format=deck["format"],
                                colors=deck["colors"],
                                strategy=deck["strategy"],
                                deck_cards=cards,
                                tags=deck.get("tags", []),
                                user_id=user_id,
                            )
                            st.success("Deck saved!")
                    except (pymongo.errors.PyMongoError, RuntimeError, ValueError) as error:
                        st.error(f"Could not save deck: {error}")

            # Compact inline Add Card form
            with st.form("add_card_form", clear_on_submit=True):
                add_col1, add_col2 = st.columns([3.5, 1])
                with add_col1:
                    card_name = st.text_input(
                        "Add a card",
                        placeholder="Add card by name…",
                        label_visibility="collapsed",
                    )
                with add_col2:
                    add_card = st.form_submit_button("Add", use_container_width=True)

            if add_card:
                card_name = card_name.strip()
                if card_name == "":
                    st.warning("Please enter a card name")
                else:
                    found = False
                    for card in cards:
                        if card["name"].lower() == card_name.lower():
                            card["qty"] += 1
                            found = True
                            break
                    if not found:
                        cards.append({"name": card_name, "qty": 1})
                    st.rerun()

            # Scrollable card list inside the deck panel
            cards_box = st.container(height=440, border=False)
            with cards_box:
                if len(cards) == 0:
                    st.info("No cards added yet")

                for i, card in enumerate(cards):
                    attach_card_image(card)
                    image_url = get_card_image_url(card)
                    c1, c2, c3, c4, c5, c6 = st.columns([1, 3.6, 0.7, 0.6, 0.7, 0.7])

                    with c1:
                        if image_url:
                            st.image(image_url, width=64)
                        else:
                            st.caption("—")
                    with c2:
                        st.markdown(f"**{card['name']}**")
                        caption_parts = []
                        if card.get("role"):
                            caption_parts.append(card["role"].capitalize())
                        if card.get("popularity_rank"):
                            caption_parts.append(f"#{card['popularity_rank']:,}")
                        if caption_parts:
                            st.caption(" · ".join(caption_parts))
                        owned_badge(owned_counts, card["name"], needed=card["qty"])
                    with c3:
                        if st.button("−", key=f"minus_{i}", disabled=card["qty"] <= 1):
                            card["qty"] -= 1
                            st.rerun()
                    with c4:
                        st.markdown(f"**{card['qty']}**")
                    with c5:
                        if st.button("+", key=f"plus_{i}"):
                            card["qty"] += 1
                            st.rerun()
                    with c6:
                        if st.button("✕", key=f"remove_{i}"):
                            cards.pop(i)
                            st.rerun()
