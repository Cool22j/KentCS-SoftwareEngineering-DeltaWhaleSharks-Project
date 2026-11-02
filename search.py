import streamlit as st
import database as db
import pymongo

def search(isEditing, deck):
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
                st.markdown("""
                <style>
                div[data-testid="stHorizontalBlock"] {
                    display: flex;
                    gap: 18px;
                    overflow-x: auto;
                    padding: 10px 4px 20px;
                    scroll-snap-type: x mandatory;
                    scrollbar-width: thin;
                    scrollbar-color: #64748b transparent;
                }

                div[data-testid="stVerticalBlockBorderWrapper"] {
                    box-sizing: border-box;
                    flex: 0 0 30%;
                    min-width: 260px;
                    max-width: 260px;
                    border: 1px solid #414856;
                    border-radius: 14px;
                    padding: 12px;
                    background: rgba(128, 128, 128, 0.06);
                    scroll-snap-align: start;
                    overflow-wrap: anywhere;
                    transition: transform 0.2s ease, box-shadow 0.2s ease,
                    border-color 0.2s ease;
                }

                div[data-testid="stVerticalBlockBorderWrapper"]:has(
                    div[data-testid="stImage"]
                ):hover {
                    transform: translateY(-6px);
                    border-color: #a78bfa;
                    box-shadow: 0 8px 24px rgba(124, 58, 237, 0.25);
                }

                div[data-testid="stVerticalBlockBorderWrapper"]  {
                    cursor: pointer;
                    border: 2px solid transparent;
                    transition: 0.2s ease;
                }

                div[data-testid="stVerticalBlockBorderWrapper"] .selected {
                    border: 2px solid #a78bfa;
                    box-shadow: 0 0 15px rgba(167, 139, 250, 0.5);
                }

                div[data-testid="stImage"]  img {
                    display: block;
                    width: 100%;
                    height: auto;
                    border-radius: 9px;
                    margin-bottom: 12px;
                }

                
                </style>
                <div class="card-row">
                """, unsafe_allow_html=True)

                #this will be the vertical scroll container
                with st.container(height = 400, border = True):
                    columns = st.columns(3)
                    for i, (card, image_url) in enumerate(results):
                        with columns[i%3]:
                            with st.container(border=True):
                                if image_url:
                                    st.image(image_url, use_container_width=True)

                                name = card.get("name", "")
                                mana_cost = card.get("mana_cost","")
                                type_line = card.get("type_line", "")
                                oracle_text = card.get("oracle_text", "")
                                
                                with st.expander(label = name, expanded = False):
                                    st.caption(f"{mana_cost}")
                                    st.caption(f"{type_line}")
                                    st.markdown(f"{oracle_text}")
                                    
                                #if editing, allow user to add cards to a deck
                                if isEditing and deck is not None:
                                    if st.button(
                                        "Add to Deck",
                                        key=f"add_{card.get('id', card['name'])}"
                                    ):
                                        existing_card = next((c for c in deck["cards"] if c["name"] == card["name"]),  None)
                                        if existing_card:
                                            existing_card["qty"] += 1
                                            st.toast(f"Increased {card['name']} quantity!")
                                        else:
                                            deck["cards"].append({
                                                "id": card.get("id"),
                                                "name": card["name"],
                                                "qty": 1,
                                                "role": "added",
                                                "image_uris": card.get("image_uris"),
                                                "card_faces": card.get("card_faces"),
                                            })
                                            st.toast(f"Added {card['name']}!")
                                        st.rerun()

            else:
                st.info("No matching cards found.")

        except (pymongo.errors.PyMongoError, RuntimeError) as error:
            st.error(f"Could not search cards: {error}")

 