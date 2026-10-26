import streamlit as st
import pymongo
import requests
import database as db
from recommendation import get_recommendations
import streamlit.components.v1 as components
import base64
from pathlib import Path


# Function to display the looping loading animation
def loading():
    video_path = Path(__file__).parent / "0000-0018.mp4"
    video_data = base64.b64encode(video_path.read_bytes()).decode("utf-8")

    components.html(
        f"""
        <div style="display:flex; justify-content:center;">
            <video autoplay loop playsinline
                   style="width:220px; max-width:100%;">
                <source
                    src="data:video/mp4;base64,{video_data}"
                    type="video/mp4">
            </video>
        </div>
        """,
        height=180,
    )

    

st.title("MTG Deck Builder")
st.write("Create a Magic: The Gathering deck using Card Shark.")

# Store the deck so it doesn't disappear when a button is clicked
if "deck" not in st.session_state:
    st.session_state["deck"] = None

st.subheader("Build Your Deck")

deck_name = st.text_input("Deck Name")

colors = st.text_input(
    "Colors (optional)",
    placeholder="Examples: Dimir, blue-black, U B, or leave blank to let AI choose",
)

deck_format = st.selectbox(
    "Format",
    ["Standard", "Modern", "Commander", "Pioneer", "Legacy", "Vintage", "Pauper"],
)

strategy = st.text_area(
    "What kind of deck do you want?",
    placeholder="Example: A deck with both control and aggro cards",
)

# Create a new deck
if st.button("Generate Deck"):
    if not strategy.strip():
        st.warning("Please enter a deck strategy")
    else:
        loader = st.empty()
        progress = st.empty()
        try:
            with loader.container():
                loading()
           
            result = get_recommendations(
                strategy,
                format=deck_format,
                colors=colors,
                progress=progress.info,
            )
            progress.empty()
            st.session_state["deck"] = {
                "name": deck_name.strip() or "Untitled Deck",
                "colors": ", ".join(result["colors"]),
                "format": deck_format,
                "strategy": result["strategy"],
                "search_logs": result.get("search_logs", []),
                "cards": result["cards"],
            }
            st.success(f"Generated a {result['total_cards']}-card deck!")
        except (ValueError, RuntimeError, requests.RequestException, pymongo.errors.PyMongoError) as error:
            progress.empty()
            st.error(f"Could not generate deck: {error}")
        loader.empty()
        progress.empty()

# Show the deck after it is created
if st.session_state["deck"] is not None:

    deck = st.session_state["deck"]
    cards = deck["cards"]

    st.subheader("Your Deck")

    st.write("Deck Name:", deck["name"])
    st.write("Format:", deck["format"])
    st.write("Colors:", deck["colors"])
    st.write("Strategy:", deck["strategy"])

    if deck.get("search_logs"):
        with st.expander("Database searches run by the chain"):
            for log_entry in deck["search_logs"]:
                st.write(f"- {log_entry}")

    st.download_button(
        "Download deck list",
        "\n".join(f"{c['qty']} {c['name']}" for c in cards),
        file_name="deck.txt",
        mime="text/plain",
    )

    # Count all the cards in the deck
    total_cards = sum(card["qty"] for card in cards)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Cards", total_cards)
    with col2:
        st.metric("Unique Cards", len(cards))

    # Add cards to the deck
    st.subheader("Add Cards")

    with st.form("add_card_form", clear_on_submit=True):
        card_name = st.text_input("Card Name")
        add_card = st.form_submit_button("Add Card")

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

    # Show cards with quantity buttons
    st.subheader("Manage Deck Cards")

    if len(cards) == 0:
        st.info("No cards added yet")

    for i, card in enumerate(cards):
        col1, col2, col3, col4, col5 = st.columns([4, 1, 1, 1, 2])

        with col1:
            st.write(card["name"])
            if card.get("role"):
                st.caption(card["role"].capitalize())

        with col2:
            if st.button("-", key=f"minus_{i}", disabled=card["qty"] <= 1):
                card["qty"] -= 1
                st.rerun()

        with col3:
            st.write(card["qty"])

        with col4:
            if st.button("+", key=f"plus_{i}"):
                card["qty"] += 1
                st.rerun()

        with col5:
            if st.button("Remove", key=f"remove_{i}"):
                cards.pop(i)
                st.rerun()

    # Save the deck to MongoDB
    if st.button("Save Deck"):
        if len(cards) == 0:
            st.warning("Add some cards before saving")
        else:
            try:
                db.save_deck(
                    name=deck["name"],
                    deck_format=deck["format"],
                    colors=deck["colors"],
                    strategy=deck["strategy"],
                    deck_cards=cards,
                    user_id=st.session_state.get("user_id"),
                )
                st.success("Deck saved successfully!")
            except (pymongo.errors.PyMongoError, RuntimeError, ValueError) as error:
                st.error(f"Could not save deck: {error}")
