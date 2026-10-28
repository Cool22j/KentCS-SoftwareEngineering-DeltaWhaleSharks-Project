import streamlit as st
import database as db
import pymongo

# Creates the main title "Card Shark"
st.image("logo.png")

# This displays the text underneath Card Shark
st.markdown(
    """<h3 style="text-align: center; font-size: 22px"> A deck builder for Magic: The Gathering </h3>""",
    unsafe_allow_html = True
)

# This displays the search bar.
st.text("Search for MTG Cards")

# Let the user switch between the two search types.
search_mode = st.segmented_control(
    "Search mode",
    ["By Name", "By Type"],
    default="By Name",
    selection_mode="single",
    label_visibility="collapsed",
    key="search_mode"
)

# Show the search box or card type options.
if search_mode == "By Name":
    query = st.text_input(
        "Search Cards",
        placeholder="Search cards by name...",
        label_visibility="collapsed",
        key="card_search"
    )
else:
    card_type = st.selectbox(
        "Card Type",
        [
            "Creature",
            "Instant",
            "Sorcery",
            "Land",
            "Enchantment",
            "Artifact",
            "Planeswalker"
        ],
        label_visibility="collapsed",
        key="card_type"
    )
    query = card_type

# This section handles the search.
if query.strip():
    try:
        # Search by name or get cards to filter by type.
        if search_mode == "By Name":
            results = db.search_cards(query, limit = 100)
        else:
            results = db.search_cards("", limit = 200, card_type = card_type)

        # Keep only one result for each card name.
        unique_cards = {}

        # Get the card name and image.
        for card in results:
            card_name = card.get("name", "")

            image_url = (card.get("image_uris") or {}).get("normal")

            if not image_url:
                faces = card.get("card_faces") or []
                if faces:
                    image_url = (
                        (faces[0].get("image_uris") or {}).get("normal")
                    )

            if card_name not in unique_cards:
                unique_cards[card_name] = (card, image_url)
            elif image_url and not unique_cards[card_name][1]:
                unique_cards[card_name] = (card, image_url)

        # Keep up to 100 unique cards in the results.
        results = list(unique_cards.values())[:100]

        # Display the results if cards were found.
        if results:
            st.markdown("### Search Results")
            st.caption(f"Found {len(results)} cards")

            import html

            cards_html = """
            <style>
            .card-row {
                display: flex;
                gap: 18px;
                overflow-x: auto;
                padding: 10px 4px 20px;
                scroll-snap-type: x mandatory;
                scrollbar-width: thin;
                scrollbar-color: #64748b transparent;
            }

            .card-item {
                box-sizing: border-box;
                flex: 0 0 30%;
                min-width: 220px;
                max-width: 280px;
                border: 1px solid #414856;
                border-radius: 14px;
                padding: 12px;
                background: rgba(128, 128, 128, 0.06);
                scroll-snap-align: start;
                overflow-wrap: anywhere;
                transition: transform 0.2s ease, box-shadow 0.2s ease,
                border-color 0.2s ease;
            }

            .card-item:hover {
                transform: translateY(-6px);
                border-color: #a78bfa;
                box-shadow: 0 8px 24px rgba(124, 58, 237, 0.25);
            }

            .card-item img {
                display: block;
                width: 100%;
                height: auto;
                border-radius: 9px;
                margin-bottom: 12px;
            }

            .card-name {
                font-size: 18px;
                font-weight: 700;
                line-height: 1.35;
                margin: 8px 0;
            }

            .card-meta {
                color: #a9b2c2;
                font-size: 13px;
                line-height: 1.5;
                margin-bottom: 8px;
            }

            .card-rules {
                font-size: 14px;
                line-height: 1.65;
                overflow-wrap: anywhere;
            }
            </style>
            <div class="card-row">
            """

            # Add each card to the results row.
            for card, image_url in results:
                name = html.escape(card.get("name", "Unknown Card"))
                mana_cost = html.escape(card.get("mana_cost", ""))
                type_line = html.escape(card.get("type_line", ""))

                # Get the card's rules text.
                raw_oracle_text = card.get("oracle_text", "")

                # Add spaces between separate lines of rules text.
                if raw_oracle_text:
                    lines = raw_oracle_text.split("\n")
                    oracle_text = "<br><br>".join(
                        html.escape(line.strip())
                        for line in lines
                        if line.strip()
                    )
                else:
                    oracle_text = ""

                cards_html += '<div class = "card-item">'

                # Display the card image if there is one.
                if image_url:
                    cards_html += (
                        f'<img src = "{html.escape(image_url, quote = True)}" '
                        f'alt = "{name}">'
                    )

                # Display the card's name.
                cards_html += f'<div class = "card-name">{name}</div>'

                # Display the card's mana cost.
                if mana_cost:
                    cards_html += (
                        f'<div class = "card-meta">{mana_cost}</div>'
                    )

                # Display the card type.
                if type_line:
                    cards_html += (
                        f'<div class = "card-meta">{type_line}</div>'
                    )

                # Display the card's rules text.
                if oracle_text:
                    cards_html += (
                        f'<div class = "card-rules">{oracle_text}</div>'
                    )

                cards_html += '</div>'

            cards_html += '</div>'

            st.html(cards_html)

        else:
            st.info("No matching cards found.")

    except (pymongo.errors.PyMongoError, RuntimeError) as error:
        st.error(f"Could not search cards: {error}")

# This adds that arrow at the bottom middle of the page, indicating the user there's more below on the landing page
st.markdown("""
<style>
.scroll-down {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 999;
    text-decoration: none !important;
    color: inherit !important;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 10px;
}

.scroll-down span {
    display: block;
    width: 16px;
    height: 16px;
    border-right: 3px solid currentColor;
    border-bottom: 3px solid currentColor;
    transform: rotate(45deg);
    animation: drift 1.8s ease-in-out infinite;
}

.scroll-down span:nth-child(2) {
    animation-delay: 0.3s;
}

@keyframes drift {
    0% {
        opacity: 0;
        transform: translateY(-5px) rotate(45deg);
    }
    50% {
        opacity: 1;
    }
    100% {
        opacity: 0;
        transform: translateY(5px) rotate(45deg);
    }
}
</style>

<a class="scroll-down" href="#shortcuts">
    <span></span>
    <span></span>
</a>
""", unsafe_allow_html=True)

# The code below creates that grid of shortcuts to navigate to the main features of our app.
st.divider()

st.markdown(
    "<h1 style='text-align: center; font-size: 50px;'>Jump right into Card Shark!</h1>",
    unsafe_allow_html = True
)

# Styles the shortcut cards to keep their size consistent; will add color later on
st.markdown("""
<style>
.shortcut-box {
    height: 210px;
    border: 1px solid rgba(128, 128, 128, 0.35);
    border-radius: 12px;
    padding: 18px 12px;
    margin-bottom: 16px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    box-sizing: border-box;
}
.shortcut-icon {
    font-size: 32px;
    margin-bottom: 8px;
}
.shortcut-title {
    font-size: 19px;
    font-weight: 600;
    margin-bottom: 6px;
}
.shortcut-description {
    font-size: 14px;
    opacity: 0.8;
    min-height: 36px;
}
</style>
""", unsafe_allow_html = True)

# This helps make the 2x2 grid for the shortcuts
col1, col2 = st.columns(2)

# Makes the left column
with col1:
    with st.container(border = True):
        st.markdown("### Build a Deck")
        st.caption("Create a new Magic Deck.")
        if st.button("Open Deck Builder", key = "shortcut_builder", use_container_width = True):
            st.switch_page("app.py")

    with st.container(border=True):
        st.markdown("### Game Rules")
        st.caption("Look up MTG rules.")
        if st.button("Read Rules", key = "shortcut_rules", use_container_width = True):
            st.switch_page("rules.py")

# Makes the right column
with col2:
    with st.container(border = True):
        st.markdown("### My Decks")
        st.caption("View and manage saved decks.")
        if st.button("View My Decks", key = "shortcut_inventory", use_container_width = True):
            st.switch_page("inventory.py")

    with st.container(border = True):
        st.markdown("### Beginner's Guide")
        st.caption("Learn the basics of MTG and deck building.")
        if st.button("Get Started", key = "shortcut_beginner", use_container_width = True):
            st.switch_page("beginner.py")

# This section displays the heading and description at the bottom of the landing page.
st.divider()

st.markdown(
    """
    <div style = "text-align: center;">
        <h1>Ready to Build Your Deck?</h1>
        <p style = "font-size: 18px;">
            Explore Magic cards, build your decks, and keep everything
            organized in one place with Card Shark.
        </p>
    </div>
    """,
    unsafe_allow_html = True
)

# This section shows the account buttons: Register / Log In, or the signed-in user.
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    if st.session_state.get("user_id"):
        st.success(f"Signed in as {st.session_state.get('username', 'user')}")
        if st.button("Manage Account", use_container_width = True):
            st.switch_page("login.py")
    else:
        if st.button("Register Now", use_container_width = True, key = "landing_register"):
            st.switch_page("login.py")
        st.markdown(
            "<p style = 'text-align: center; font-size: 13px; margin-top: 8px;'>"
            "Already have an account?</p>",
            unsafe_allow_html = True
        )
        if st.button("Log In", use_container_width = True, key = "landing_login"):
            st.switch_page("login.py")