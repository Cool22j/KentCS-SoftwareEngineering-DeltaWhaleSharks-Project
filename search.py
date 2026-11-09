import html
import streamlit as st
import database as db
import pymongo

CARDS_PER_ROW = 7
ROWS_PER_PAGE = 3
CARDS_PER_PAGE = CARDS_PER_ROW * ROWS_PER_PAGE  # 21 cards per page

_CARD_TILE_HTML = '<div class="card-root"></div>'

_CARD_TILE_CSS = """
.card-root {
    padding: 4px;
    box-sizing: border-box;
    width: 100%;
}

.card-btn {
    display: block;
    width: 100%;
    padding: 0;
    margin: 0;
    border: 1px solid rgba(148, 163, 184, 0.28);
    border-radius: 10px;
    background: rgba(15, 23, 42, 0.14);
    cursor: pointer;
    overflow: hidden;
    aspect-ratio: 488 / 680;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.35);
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.card-btn:hover,
.card-btn:focus-visible {
    transform: translateY(-4px) scale(1.02);
    border-color: var(--card-highlight-border, #a78bfa);
    box-shadow: var(--card-highlight-shadow, 0 10px 22px rgba(124, 58, 237, 0.45));
    outline: none;
}

.card-btn:active {
    transform: translateY(-1px) scale(0.99);
}

.card-btn img {
    display: block;
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 9px;
}

.card-fallback {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 6px;
    padding: 10px;
    box-sizing: border-box;
    text-align: center;
    color: var(--st-text-color, #e2e8f0);
    background: rgba(100, 116, 139, 0.14);
}

.card-fallback-name {
    font-family: var(--st-font, sans-serif);
    font-size: 13px;
    font-weight: 600;
    line-height: 1.25;
    word-break: break-word;
}

.card-fallback-note {
    font-family: var(--st-font, sans-serif);
    font-size: 11px;
    opacity: 0.7;
}
"""

_CARD_TILE_JS = """
export default function(component) {
    const { data, setTriggerValue, parentElement } = component;
    const root = parentElement.querySelector('.card-root');
    if (!root) return;

    root.innerHTML = '';

    const cardData = data || {};
    const cardName = cardData.name || 'Unknown Card';

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'card-btn';
    btn.title = cardName;
    btn.setAttribute('aria-label', `Inspect ${cardName}`);
    if (cardData.highlight_border) {
        btn.style.setProperty('--card-highlight-border', cardData.highlight_border);
    }
    if (cardData.highlight_shadow) {
        btn.style.setProperty('--card-highlight-shadow', cardData.highlight_shadow);
    }

    const createFallback = () => {
        const fallback = document.createElement('div');
        fallback.className = 'card-fallback';

        const title = document.createElement('div');
        title.className = 'card-fallback-name';
        title.textContent = cardName;

        const note = document.createElement('div');
        note.className = 'card-fallback-note';
        note.textContent = 'No Image Available';

        fallback.appendChild(title);
        fallback.appendChild(note);
        return fallback;
    };

    if (cardData.image_url) {
        const img = document.createElement('img');
        img.src = cardData.image_url;
        img.alt = cardName;
        img.loading = 'lazy';
        img.onerror = () => {
            btn.innerHTML = '';
            btn.appendChild(createFallback());
        };
        btn.appendChild(img);
    } else {
        btn.appendChild(createFallback());
    }

    btn.onclick = () => {
        setTriggerValue('clicked', cardData.card_idx);
    };

    root.appendChild(btn);

    return () => {
        root.innerHTML = '';
    };
}
"""

_clickable_card = st.components.v2.component(
    "card_shark_clickable_card",
    html=_CARD_TILE_HTML,
    css=_CARD_TILE_CSS,
    js=_CARD_TILE_JS,
)


def get_card_image_url(card, face_idx=0, preferred_sizes=("normal", "small", "large")):
    """Safely extract image URL from standard or multi-faced card data."""
    faces = card.get("card_faces")
    if isinstance(faces, list) and 0 <= face_idx < len(faces) and isinstance(faces[face_idx], dict):
        face_uris = faces[face_idx].get("image_uris")
        if isinstance(face_uris, dict):
            for size in preferred_sizes:
                if face_uris.get(size):
                    return face_uris[size]

    image_uris = card.get("image_uris")
    if isinstance(image_uris, dict):
        for size in preferred_sizes:
            if image_uris.get(size):
                return image_uris[size]

    if isinstance(faces, list) and faces and isinstance(faces[0], dict):
        face_uris = faces[0].get("image_uris")
        if isinstance(face_uris, dict):
            for size in preferred_sizes:
                if face_uris.get(size):
                    return face_uris[size]

    return None


def _has_two_image_faces(card):
    """Return True if card has separate image URIs on at least two faces."""
    faces = card.get("card_faces")
    if not isinstance(faces, list) or len(faces) < 2:
        return False
    return (
        isinstance(faces[0], dict)
        and isinstance(faces[1], dict)
        and isinstance(faces[0].get("image_uris"), dict)
        and isinstance(faces[1].get("image_uris"), dict)
    )


_ELEMENTAL_COLORS = {
    "W": {
        "border": "#fef3c7",
        "glow": "rgba(253, 230, 138, 0.65)",
        "accent": "#eab308",
    },
    "U": {
        "border": "#38bdf8",
        "glow": "rgba(56, 189, 248, 0.58)",
        "accent": "#38bdf8",
    },
    "B": {
        "border": "#a855f7",
        "glow": "rgba(168, 85, 247, 0.58)",
        "accent": "#a855f7",
    },
    "R": {
        "border": "#ef4444",
        "glow": "rgba(239, 68, 68, 0.58)",
        "accent": "#ef4444",
    },
    "G": {
        "border": "#22c55e",
        "glow": "rgba(34, 197, 94, 0.58)",
        "accent": "#22c55e",
    },
}

_GOLD_STYLE = {
    "border": "#eab308",
    "glow": "rgba(234, 179, 8, 0.56)",
    "accent": "#eab308",
}

_COLORLESS_STYLE = {
    "border": "#cbd5e1",
    "glow": "rgba(203, 213, 225, 0.48)",
    "accent": "#94a3b8",
}


def get_card_colors(card, face_idx=None):
    """Determine MTG elemental color codes (W, U, B, R, G) for a card or active face."""
    faces = card.get("card_faces")
    raw_colors = None

    if (
        face_idx is not None
        and isinstance(faces, list)
        and 0 <= face_idx < len(faces)
        and isinstance(faces[face_idx], dict)
    ):
        raw_colors = faces[face_idx].get("colors")

    if raw_colors is None:
        raw_colors = card.get("colors")

    if raw_colors is None and isinstance(faces, list):
        collected = []
        for face in faces:
            if isinstance(face, dict):
                for c in face.get("colors") or []:
                    if c in _ELEMENTAL_COLORS and c not in collected:
                        collected.append(c)
        raw_colors = collected

    colors = [c for c in (raw_colors or []) if c in _ELEMENTAL_COLORS]

    type_line = ""
    if (
        face_idx is not None
        and isinstance(faces, list)
        and 0 <= face_idx < len(faces)
        and isinstance(faces[face_idx], dict)
    ):
        type_line = faces[face_idx].get("type_line", "")
    if not type_line:
        type_line = card.get("type_line", "")

    # Lands are colorless by rule, so fall back to color_identity / produced_mana
    if not colors and "land" in type_line.lower():
        identity = card.get("color_identity") or []
        colors = [c for c in identity if c in _ELEMENTAL_COLORS]
        if not colors:
            produced = card.get("produced_mana") or []
            colors = [c for c in produced if c in _ELEMENTAL_COLORS]

    return colors


def get_card_highlight_style(card, face_idx=None):
    """Return elemental border color, glow box-shadow, and accent color for a card."""
    colors = get_card_colors(card, face_idx=face_idx)

    if len(colors) == 1:
        spec = _ELEMENTAL_COLORS[colors[0]]
        return {
            "border": spec["border"],
            "shadow": f"0 10px 24px {spec['glow']}",
            "accent": spec["accent"],
        }

    if len(colors) == 2:
        c1 = _ELEMENTAL_COLORS[colors[0]]
        c2 = _ELEMENTAL_COLORS[colors[1]]
        return {
            "border": _GOLD_STYLE["border"],
            "shadow": f"-4px -4px 18px {c1['glow']}, 4px 4px 18px {c2['glow']}, 0 8px 20px rgba(0, 0, 0, 0.45)",
            "accent": _GOLD_STYLE["accent"],
        }

    if len(colors) >= 3:
        return {
            "border": _GOLD_STYLE["border"],
            "shadow": f"0 10px 24px {_GOLD_STYLE['glow']}",
            "accent": _GOLD_STYLE["accent"],
        }

    return {
        "border": _COLORLESS_STYLE["border"],
        "shadow": f"0 10px 22px {_COLORLESS_STYLE['glow']}",
        "accent": _COLORLESS_STYLE["accent"],
    }


def _escape_html_text(text):
    """Escape HTML characters and dollar signs so KaTeX math isn't triggered."""
    return html.escape(str(text)).replace("$", "&#36;")


def _add_card_to_deck(card, deck):
    """Add one copy of card to deck or increment quantity if already present."""
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


def _render_face_block(face, show_heading=True, accent_color="#a78bfa"):
    """Render name, cost, type line, oracle text, stats, and flavor for one face."""
    face_name = face.get("name", "Unknown")
    mana_cost = face.get("mana_cost", "")
    type_line = face.get("type_line", "")
    oracle_text = face.get("oracle_text", "")
    power = face.get("power")
    toughness = face.get("toughness")
    loyalty = face.get("loyalty")
    defense = face.get("defense")
    flavor_text = face.get("flavor_text", "")

    if show_heading:
        header_html = f"<div style='font-size: 22px; font-weight: 700; line-height: 1.25; margin-bottom: 4px;'>{_escape_html_text(face_name)}"
        if mana_cost:
            header_html += (
                f" <span style='font-size: 15px; font-weight: 600; color: {accent_color}; "
                f"margin-left: 6px;'>{_escape_html_text(mana_cost)}</span>"
            )
        header_html += "</div>"
        st.markdown(header_html, unsafe_allow_html=True)

    if type_line:
        st.markdown(
            f"<div style='font-size: 14px; font-weight: 600; color: #94a3b8; margin-bottom: 10px;'>"
            f"{_escape_html_text(type_line)}</div>",
            unsafe_allow_html=True,
        )

    if oracle_text:
        formatted_oracle = _escape_html_text(oracle_text).replace("\n", "<br>")
        st.markdown(
            f"<div style='font-size: 14px; line-height: 1.5; padding: 10px 12px; "
            f"border-radius: 8px; background: rgba(148, 163, 184, 0.1); "
            f"border-left: 3px solid {accent_color}; margin-bottom: 10px;'>{formatted_oracle}</div>",
            unsafe_allow_html=True,
        )

    stats_parts = []
    if power is not None and toughness is not None:
        stats_parts.append(f"<b>Power / Toughness:</b> {_escape_html_text(power)} / {_escape_html_text(toughness)}")
    if loyalty is not None:
        stats_parts.append(f"<b>Loyalty:</b> {_escape_html_text(loyalty)}")
    if defense is not None:
        stats_parts.append(f"<b>Defense:</b> {_escape_html_text(defense)}")
    if stats_parts:
        st.markdown(
            f"<div style='font-size: 14px; margin-bottom: 8px;'>{' &nbsp;&bull;&nbsp; '.join(stats_parts)}</div>",
            unsafe_allow_html=True,
        )

    if flavor_text:
        formatted_flavor = _escape_html_text(flavor_text).replace("\n", "<br>")
        st.markdown(
            f"<div style='font-size: 13px; font-style: italic; opacity: 0.8; margin-bottom: 8px;'>"
            f"{formatted_flavor}</div>",
            unsafe_allow_html=True,
        )


@st.dialog("Card Details", width="medium")
def show_focused_card(card, isEditing=False, deck=None, prefix="landing_"):
    """Focus the clicked card in a centered modal and display its full details."""
    has_two_image_faces = _has_two_image_faces(card)
    face_state_key = f"{prefix}focused_face_idx"
    face_idx = st.session_state.get(face_state_key, 0) if has_two_image_faces else 0
    if has_two_image_faces and face_idx not in (0, 1):
        face_idx = 0

    highlight = get_card_highlight_style(
        card,
        face_idx=face_idx if has_two_image_faces else None,
    )

    st.markdown(
        f"""
        <style>
        div[data-testid="stDialog"] div[data-testid="stImage"] img {{
            border-radius: 12px !important;
            border: 2px solid {highlight["border"]} !important;
            box-shadow: {highlight["shadow"]};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    img_col, info_col = st.columns([1, 1.35], gap="medium")

    with img_col:
        focused_img = get_card_image_url(
            card,
            face_idx=face_idx,
            preferred_sizes=("large", "normal", "small"),
        )
        if focused_img:
            st.image(focused_img, width="stretch")
        else:
            st.markdown(
                f"<div style='height: 320px; display: flex; flex-direction: column; align-items: center; "
                f"justify-content: center; border-radius: 12px; border: 1px dashed rgba(148,163,184,0.4); "
                f"background: rgba(100,116,139,0.12); padding: 16px; text-align: center;'>"
                f"<div style='font-weight: 700; margin-bottom: 6px;'>{_escape_html_text(card.get('name', 'Unknown'))}</div>"
                f"<div style='font-size: 12px; opacity: 0.7;'>No Image Available</div></div>",
                unsafe_allow_html=True,
            )

        if has_two_image_faces:
            def _flip_face():
                st.session_state[face_state_key] = 1 - st.session_state.get(face_state_key, 0)

            other_face_name = card["card_faces"][1 - face_idx].get("name", "Other Side")
            st.button(
                f"🔄 Flip to {other_face_name}",
                key=f"{prefix}dialog_flip_btn",
                on_click=_flip_face,
                use_container_width=True,
            )

        if isEditing and deck is not None:
            if st.button("Add to Deck", key=f"{prefix}dialog_add_btn", type="primary", use_container_width=True):
                _add_card_to_deck(card, deck)
                st.rerun()

    with info_col:
        faces = card.get("card_faces")
        if has_two_image_faces:
            _render_face_block(faces[face_idx], show_heading=True, accent_color=highlight["accent"])
        elif isinstance(faces, list) and len(faces) > 1:
            for idx, face in enumerate(faces):
                if isinstance(face, dict):
                    if idx > 0:
                        st.divider()
                    _render_face_block(face, show_heading=True, accent_color=highlight["accent"])
        else:
            _render_face_block(card, show_heading=True, accent_color=highlight["accent"])

        # Metadata section (set, rarity, mana value, artist, price, legalities)
        meta_rows = []
        set_name = card.get("set_name")
        set_code = card.get("set", "")
        collector_num = card.get("collector_number", "")
        if set_name:
            set_label = _escape_html_text(set_name)
            extra = " ".join(
                part
                for part in (
                    f"({_escape_html_text(set_code.upper())})" if set_code else "",
                    f"#{_escape_html_text(collector_num)}" if collector_num else "",
                )
                if part
            )
            if extra:
                set_label = f"{set_label} <span style='opacity: 0.75;'>{extra}</span>"
            meta_rows.append(f"<b>Set:</b> {set_label}")

        rarity = card.get("rarity")
        if rarity:
            meta_rows.append(f"<b>Rarity:</b> {_escape_html_text(rarity.capitalize())}")

        cmc = card.get("cmc")
        if cmc is not None:
            cmc_display = int(cmc) if isinstance(cmc, float) and cmc.is_integer() else cmc
            meta_rows.append(f"<b>Mana Value:</b> {_escape_html_text(cmc_display)}")

        artist = card.get("artist")
        if artist:
            meta_rows.append(f"<b>Artist:</b> {_escape_html_text(artist)}")

        usd_price = (card.get("prices") or {}).get("usd") if isinstance(card.get("prices"), dict) else None
        if usd_price:
            meta_rows.append(f"<b>Price (USD):</b> &#36;{_escape_html_text(usd_price)}")

        if meta_rows:
            st.divider()
            st.markdown(
                "<div style='font-size: 13px; line-height: 1.7;'>" + "<br>".join(meta_rows) + "</div>",
                unsafe_allow_html=True,
            )

        legalities = card.get("legalities")
        if isinstance(legalities, dict):
            key_formats = [
                ("standard", "Standard"),
                ("pioneer", "Pioneer"),
                ("modern", "Modern"),
                ("legacy", "Legacy"),
                ("commander", "Commander"),
                ("pauper", "Pauper"),
            ]
            badges = []
            status_styles = {
                "legal": ("rgba(34, 197, 94, 0.18)", "#4ade80", "Legal"),
                "restricted": ("rgba(234, 179, 8, 0.18)", "#facc15", "Restricted"),
                "banned": ("rgba(239, 68, 68, 0.18)", "#f87171", "Banned"),
                "not_legal": ("rgba(148, 163, 184, 0.12)", "#94a3b8", "Not Legal"),
            }
            for fmt_key, fmt_label in key_formats:
                status = legalities.get(fmt_key)
                if status in status_styles:
                    bg, fg, status_text = status_styles[status]
                    badges.append(
                        f"<span style='display: inline-block; padding: 2px 8px; margin: 2px 4px 2px 0; "
                        f"border-radius: 999px; font-size: 11px; font-weight: 600; "
                        f"background: {bg}; color: {fg}; border: 1px solid {fg}33;' "
                        f"title='{fmt_label}: {status_text}'>{fmt_label}: {status_text}</span>"
                    )
            if badges:
                st.markdown(
                    "<div style='margin-top: 10px;'>"
                    "<div style='font-size: 12px; font-weight: 600; opacity: 0.8; margin-bottom: 4px;'>Format Legalities</div>"
                    + "".join(badges)
                    + "</div>",
                    unsafe_allow_html=True,
                )


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

                # Header info and pagination
                if total_pages > 1:
                    top_col1, top_col2, top_col3, top_col4 = st.columns([3, 1.2, 2, 1.2])

                    with top_col1:
                        st.markdown(
                            f"<div style='line-height: 2.4; font-size: 15px; font-weight: 600;'>"
                            f"Search Results <span style='color: #94a3b8; font-weight: 400; font-size: 13px;'>"
                            f"({total_cards} cards found &bull; showing {start_idx + 1}–{end_idx} &bull; Click any card for details)</span></div>",
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
                        f"({total_cards} cards found &bull; Click any card for details)</span></div>",
                        unsafe_allow_html=True,
                    )

                clicked_card = None

                # Card Grid: Up to 3 rows of 7 columns
                for r in range(ROWS_PER_PAGE):
                    row_slice = page_cards[r * CARDS_PER_ROW : (r + 1) * CARDS_PER_ROW]
                    if not row_slice:
                        break

                    cols = st.columns(CARDS_PER_ROW)

                    for c, (card, image_url) in enumerate(row_slice):
                        card_idx = start_idx + r * CARDS_PER_ROW + c
                        name = card.get("name", "Unknown")
                        highlight = get_card_highlight_style(
                            card,
                            face_idx=0 if _has_two_image_faces(card) else None,
                        )

                        with cols[c]:
                            tile_res = _clickable_card(
                                key=f"{prefix}card_tile_{r}_{c}",
                                data={
                                    "name": name,
                                    "image_url": image_url,
                                    "card_idx": card_idx,
                                    "highlight_border": highlight["border"],
                                    "highlight_shadow": highlight["shadow"],
                                },
                                on_clicked_change=lambda: None,
                                width="stretch",
                                height="content",
                            )
                            if (
                                tile_res.clicked is not None
                                and isinstance(tile_res.clicked, int)
                                and 0 <= tile_res.clicked < total_cards
                            ):
                                clicked_card = results[tile_res.clicked][0]

                            # If editing, allow user to add cards to a deck
                            if isEditing and deck is not None:
                                btn_key = f"{prefix}add_{card.get('id', name)}_{card_idx}"
                                if st.button("Add to Deck", key=btn_key, use_container_width=True):
                                    _add_card_to_deck(card, deck)
                                    st.rerun()

                if clicked_card is not None:
                    st.session_state[f"{prefix}focused_face_idx"] = 0
                    show_focused_card(
                        clicked_card,
                        isEditing=isEditing,
                        deck=deck,
                        prefix=prefix,
                    )

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
