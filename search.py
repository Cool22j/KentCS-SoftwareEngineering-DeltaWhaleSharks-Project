import html
import streamlit as st
import database as db
import pymongo

CARDS_PER_ROW = 7
ROWS_PER_PAGE = 3
CARDS_PER_PAGE = CARDS_PER_ROW * ROWS_PER_PAGE  # 21 cards per page


def get_card_image_url(card):
    """Safely extract image URL from standard or multi-faced card data."""
    image_uris = card.get("image_uris")
    if isinstance(image_uris, dict):
        url = (
            image_uris.get("normal")
            or image_uris.get("small")
            or image_uris.get("large")
        )
        if url:
            return url

    faces = card.get("card_faces")
    if isinstance(faces, list) and len(faces) > 0 and isinstance(faces[0], dict):
        face_uris = faces[0].get("image_uris")
        if isinstance(face_uris, dict):
            url = (
                face_uris.get("normal")
                or face_uris.get("small")
                or face_uris.get("large")
            )
            if url:
                return url

    return None


def search(isEditing=False, deck=None):
    prefix = "edit_" if isEditing else "landing_"

    # Let the user switch between the two search types.
    search_mode = st.segmented_control(
        "Search mode",
        ["By Name", "By Type"],
        default="By Name",
        selection_mode="single",
        label_visibility="collapsed",
        key=f"{prefix}search_mode",
    )

    # Show the search box or card type options.
    if search_mode == "By Name":
        query = st.text_input(
            "Search Cards",
            placeholder="Search cards by name...",
            label_visibility="collapsed",
            key=f"{prefix}card_search",
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
                "Planeswalker",
            ],
            label_visibility="collapsed",
            key=f"{prefix}card_type",
        )
        query = card_type

    # This section handles the search.
    if query and query.strip():
        try:
            # Search by name or get cards to filter by type.
            if search_mode == "By Name":
                raw_results = db.search_cards(query, limit=350)
            else:
                raw_results = db.search_cards("", limit=500, card_type=card_type)

            # Keep only one result for each card name, preferring printings with images.
            unique_cards = {}
            for card in raw_results:
                card_name = card.get("name", "")
                if not card_name:
                    continue
                image_url = get_card_image_url(card)
                if card_name not in unique_cards:
                    unique_cards[card_name] = (card, image_url)
                elif image_url and not unique_cards[card_name][1]:
                    unique_cards[card_name] = (card, image_url)

            results = list(unique_cards.values())

            # Display the results if cards were found.
            if results:
                total_cards = len(results)
                total_pages = max(1, (total_cards + CARDS_PER_PAGE - 1) // CARDS_PER_PAGE)

                # Reset page to 1 whenever search query or mode changes
                query_track_key = f"{prefix}last_search_query"
                page_state_key = f"{prefix}search_page"
                current_query_sig = f"{search_mode}:{query.strip().lower()}"

                if st.session_state.get(query_track_key) != current_query_sig:
                    st.session_state[query_track_key] = current_query_sig
                    st.session_state[page_state_key] = 1

                current_page = st.session_state.get(page_state_key, 1)
                current_page = max(1, min(current_page, total_pages))
                st.session_state[page_state_key] = current_page

                start_idx = (current_page - 1) * CARDS_PER_PAGE
                end_idx = min(start_idx + CARDS_PER_PAGE, total_cards)
                page_cards = results[start_idx:end_idx]

                # Scoped CSS styling for 7-column card grid
                st.markdown(
                    """
                    <style>
                    /* Card Shark 7-Column Search Grid Styling */
                    div[data-testid="column"] img {
                        border-radius: 8px !important;
                        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.4);
                        transition: transform 0.18s ease, box-shadow 0.18s ease;
                    }

                    div[data-testid="column"] img:hover {
                        transform: translateY(-3px) scale(1.02);
                        box-shadow: 0 8px 18px rgba(124, 58, 237, 0.35);
                    }

                    /* Compact expander details in 7-column view */
                    div[data-testid="column"] div[data-testid="stExpander"] details summary {
                        font-size: 11px !important;
                        padding: 3px 6px !important;
                    }

                    div[data-testid="column"] div[data-testid="stExpander"] details summary p {
                        font-size: 11px !important;
                        overflow: hidden !important;
                        text-overflow: ellipsis !important;
                        white-space: nowrap !important;
                    }

                    div[data-testid="column"] div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
                        padding: 6px !important;
                        font-size: 11px !important;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True,
                )

                # Header info and pagination
                if total_pages > 1:
                    top_col1, top_col2, top_col3, top_col4 = st.columns([3, 1.2, 2, 1.2])

                    with top_col1:
                        st.markdown(
                            f"<div style='line-height: 2.4; font-size: 15px; font-weight: 600;'>"
                            f"Search Results <span style='color: #94a3b8; font-weight: 400; font-size: 13px;'>"
                            f"({total_cards} cards found &bull; showing {start_idx + 1}–{end_idx})</span></div>",
                            unsafe_allow_html=True,
                        )

                    with top_col2:
                        if st.button("◀ Prev", disabled=(current_page <= 1), key=f"{prefix}prev_top", use_container_width=True):
                            st.session_state[page_state_key] = current_page - 1
                            st.rerun()

                    with top_col3:
                        st.markdown(
                            f"<div style='text-align: center; line-height: 2.4; font-weight: 600; font-size: 13px;'>"
                            f"Page {current_page} of {total_pages}</div>",
                            unsafe_allow_html=True,
                        )

                    with top_col4:
                        if st.button("Next ▶", disabled=(current_page >= total_pages), key=f"{prefix}next_top", use_container_width=True):
                            st.session_state[page_state_key] = current_page + 1
                            st.rerun()
                else:
                    st.markdown(
                        f"<div style='line-height: 2.4; font-size: 15px; font-weight: 600;'>"
                        f"Search Results <span style='color: #94a3b8; font-weight: 400; font-size: 13px;'>"
                        f"({total_cards} cards found)</span></div>",
                        unsafe_allow_html=True,
                    )

                # Card Grid: Up to 3 rows of 7 columns
                for r in range(ROWS_PER_PAGE):
                    row_slice = page_cards[r * CARDS_PER_ROW : (r + 1) * CARDS_PER_ROW]
                    if not row_slice:
                        break

                    cols = st.columns(CARDS_PER_ROW)

                    for c, (card, image_url) in enumerate(row_slice):
                        with cols[c]:
                            with st.container(border=True):
                                if image_url:
                                    st.image(image_url, use_container_width=True)
                                else:
                                    st.markdown(
                                        """<div style='height: 180px; display: flex; align-items: center; justify-content: center; background: rgba(128,128,128,0.1); border-radius: 8px; border: 1px dashed rgba(128,128,128,0.3); color: #888; font-size: 11px; text-align: center; padding: 6px;'>No Image Available</div>""",
                                        unsafe_allow_html=True,
                                    )

                                name = card.get("name", "Unknown")
                                mana_cost = card.get("mana_cost", "")
                                type_line = card.get("type_line", "")
                                oracle_text = card.get("oracle_text", "")

                                with st.expander(label=name, expanded=False):
                                    st.markdown(f"**{html.escape(name)}**")
                                    if mana_cost:
                                        st.caption(f"**Cost:** {html.escape(mana_cost)}")
                                    if type_line:
                                        st.caption(f"**Type:** {html.escape(type_line)}")
                                    if oracle_text:
                                        safe_text = html.escape(oracle_text).replace("$", "\\$")
                                        st.markdown(
                                            f"<div style='font-size: 11px; line-height: 1.3;'>{safe_text}</div>",
                                            unsafe_allow_html=True,
                                        )

                                # If editing, allow user to add cards to a deck
                                if isEditing and deck is not None:
                                    card_idx = start_idx + r * CARDS_PER_ROW + c
                                    btn_key = f"{prefix}add_{card.get('id', card.get('name', ''))}_{card_idx}"
                                    if st.button("Add to Deck", key=btn_key, use_container_width=True):
                                        existing_card = next(
                                            (cd for cd in deck["cards"] if cd["name"] == card["name"]),
                                            None,
                                        )
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

                # Bottom pagination controls
                if total_pages > 1:
                    st.write("")
                    bot_col1, bot_col2, bot_col3, bot_col4, bot_col5 = st.columns([1, 1.2, 2.5, 1.2, 1])

                    with bot_col1:
                        if st.button("⏮ First", disabled=(current_page <= 1), key=f"{prefix}first_bot", use_container_width=True):
                            st.session_state[page_state_key] = 1
                            st.rerun()

                    with bot_col2:
                        if st.button("◀ Prev", disabled=(current_page <= 1), key=f"{prefix}prev_bot", use_container_width=True):
                            st.session_state[page_state_key] = current_page - 1
                            st.rerun()

                    with bot_col3:
                        st.markdown(
                            f"<div style='text-align: center; line-height: 2.4; font-size: 14px; font-weight: 600;'>"
                            f"Page {current_page} of {total_pages} &nbsp;&bull;&nbsp; "
                            f"<span style='color: #94a3b8; font-weight: 400; font-size: 12px;'>Showing {start_idx + 1}–{end_idx} of {total_cards}</span>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )

                    with bot_col4:
                        if st.button("Next ▶", disabled=(current_page >= total_pages), key=f"{prefix}next_bot", use_container_width=True):
                            st.session_state[page_state_key] = current_page + 1
                            st.rerun()

                    with bot_col5:
                        if st.button("Last ⏭", disabled=(current_page >= total_pages), key=f"{prefix}last_bot", use_container_width=True):
                            st.session_state[page_state_key] = total_pages
                            st.rerun()

                    if total_pages > 2:
                        jump_col1, jump_col2, jump_col3 = st.columns([2, 1.5, 2])
                        with jump_col2:
                            jump_page = st.selectbox(
                                "Go to page",
                                options=list(range(1, total_pages + 1)),
                                index=current_page - 1,
                                key=f"{prefix}jump_page_select_{current_page}",
                                label_visibility="collapsed",
                            )
                            if jump_page != current_page:
                                st.session_state[page_state_key] = jump_page
                                st.rerun()

            else:
                st.info("No matching cards found.")

        except (pymongo.errors.PyMongoError, RuntimeError) as error:
            st.error(f"Could not search cards: {error}")
