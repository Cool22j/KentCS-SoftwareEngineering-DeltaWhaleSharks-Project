import html

import streamlit as st
import pymongo

import database as db
import user_database as udb

CARDS_PER_ROW = 5
CARDS_PER_PAGE = 20

st.markdown(
    "<h1 style='text-align: center;'>My Collection</h1>",
    unsafe_allow_html=True,
)

user_id = st.session_state.get("user_id")

if not user_id:
    st.info("Log in to keep track of the cards you own.")
    st.page_link("login.py", label="Log In / Register", icon=":material/person:")
    st.stop()


def _set_label(card):
    """'Magic 2010 #146' when the card has set info, otherwise an empty string."""
    set_name = card.get("set_name") or (card.get("set") or "").upper()
    number = card.get("collector_number") or ""
    if not set_name:
        return ""
    return f"{set_name} #{number}" if number else set_name


def _picker_label(card):
    """Label for the dropdown: the printing if we know it, otherwise the card type."""
    detail = _set_label(card) or card.get("type_line", "")
    return f"{card.get('name', 'Unknown')} ({detail})" if detail else card.get("name", "Unknown")


def _picker_options(results):
    """One option per printing when the catalog has set info, else one per card name."""
    if any(_set_label(card) for card in results):
        return [card for card in results if card.get("id")]
    # No set info: keep one printing per name, always the same one (lowest id),
    # so adding a card twice stacks the count instead of creating a second entry.
    by_name = {}
    for card in results:
        name, card_id = card.get("name"), card.get("id")
        if name and card_id and (name not in by_name or card_id < by_name[name]["id"]):
            by_name[name] = card
    return sorted(by_name.values(), key=lambda card: card["name"])


# ADD CARDS

with st.container(border=True):
    st.subheader("Add cards")
    search_text = st.text_input(
        "Card name",
        placeholder="Type at least 2 letters, e.g. Lightning Bolt",
        key="collection_search",
    )

    if len(search_text.strip()) >= 2:
        try:
            results = _picker_options(db.search_cards(search_text, limit=200))
        except (pymongo.errors.PyMongoError, RuntimeError) as error:
            st.error(f"Could not search cards: {error}")
            results = []

        if not results:
            st.info("No cards match that name. Check the spelling and try again.")
        else:
            preview_col, form_col = st.columns([1, 5])
            with form_col:
                pick_col, qty_col, add_col = st.columns([4, 1, 1.4], vertical_alignment="bottom")
                with pick_col:
                    picked = st.selectbox(
                        "Card",
                        results,
                        format_func=_picker_label,
                        key="collection_pick",
                    )
                with qty_col:
                    add_qty = st.number_input("Copies", min_value=1, max_value=99, value=1, key="collection_qty")
                with add_col:
                    if st.button("Add", type="primary", use_container_width=True):
                        try:
                            udb.add_to_collection(user_id, picked, int(add_qty))
                        except ValueError as error:
                            st.error(str(error))
                        except (pymongo.errors.PyMongoError, RuntimeError) as error:
                            st.error(f"Could not add the card: {error}")
                        else:
                            st.toast(f"Added {int(add_qty)} × {picked['name']}")
                            st.rerun()

            with preview_col:
                image_url = udb._card_image_url(picked)
                if image_url:
                    st.image(image_url, width=120)


# YOUR CARDS

try:
    owned = udb.get_collection(user_id)
except (pymongo.errors.PyMongoError, RuntimeError) as error:
    st.error(f"Could not load your collection: {error}")
    st.stop()

if not owned:
    st.info("Your collection is empty. Search for a card above to add it.")
    st.stop()

total_copies = sum(card["qty"] for card in owned)
unique_names = len({card["name"] for card in owned})
total_value = sum((card.get("price_usd") or 0) * card["qty"] for card in owned)

has_prices = any(card.get("price_usd") for card in owned)
m1, m2, m3 = st.columns(3) if has_prices else (*st.columns(2), None)
m1.metric("Total cards", f"{total_copies:,}")
m2.metric("Unique cards", f"{unique_names:,}")
if m3:
    m3.metric("Estimated value", f"${total_value:,.2f}", help="Based on Scryfall USD prices from when each card was added.")

filter_col, sort_col = st.columns([3, 1])
with filter_col:
    name_filter = st.text_input(
        "Filter your cards",
        placeholder="Filter by name or type...",
        label_visibility="collapsed",
        key="collection_filter",
    )
with sort_col:
    sort_by = st.selectbox(
        "Sort by",
        ["Name", "Most copies", "Highest value", "Recently added"],
        label_visibility="collapsed",
        key="collection_sort",
    )

needle = name_filter.strip().lower()
shown = [
    card for card in owned
    if not needle or needle in card["name"].lower() or needle in card.get("type_line", "").lower()
]

if sort_by == "Most copies":
    shown.sort(key=lambda card: card["qty"], reverse=True)
elif sort_by == "Highest value":
    shown.sort(key=lambda card: card.get("price_usd") or 0, reverse=True)
elif sort_by == "Recently added":
    shown.sort(key=lambda card: card.get("added_at") or 0, reverse=True)

if not shown:
    st.info("None of your cards match that filter.")
    st.stop()

# Paging, reset to page 1 whenever the filter or sort changes
view_sig = f"{needle}|{sort_by}"
if st.session_state.get("collection_view") != view_sig:
    st.session_state["collection_view"] = view_sig
    st.session_state["collection_page"] = 1

total_pages = max(1, (len(shown) + CARDS_PER_PAGE - 1) // CARDS_PER_PAGE)
page = max(1, min(st.session_state.get("collection_page", 1), total_pages))
start = (page - 1) * CARDS_PER_PAGE
page_cards = shown[start:start + CARDS_PER_PAGE]


def _change_qty(card_id, new_qty):
    try:
        udb.set_owned_qty(user_id, card_id, new_qty)
    except (pymongo.errors.PyMongoError, RuntimeError) as error:
        st.error(f"Could not update the card: {error}")
    else:
        st.rerun()


st.markdown(
    """
    <style>
    .owned-name { font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .owned-meta { font-size: 0.85rem; opacity: 0.65; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .owned-qty { text-align: center; line-height: 2.5rem; font-weight: 600; position: relative; top: -0.5rem; }
    .owned-qty, .owned-meta, .owned-name { margin: 0; }
    /* keep the − qty + row on one line on phones instead of stacking */
    div[data-testid="stHorizontalBlock"]:has(.owned-qty):not(:has(div[data-testid="stHorizontalBlock"])) { flex-wrap: nowrap !important; gap: 0.5rem; }
    div[data-testid="stHorizontalBlock"]:has(.owned-qty):not(:has(div[data-testid="stHorizontalBlock"])) > div { min-width: 0 !important; flex: 1 1 0 !important; width: auto !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

for row_start in range(0, len(page_cards), CARDS_PER_ROW):
    cols = st.columns(CARDS_PER_ROW)
    for col, card in zip(cols, page_cards[row_start:row_start + CARDS_PER_ROW]):
        card_id = card["card_id"]
        with col, st.container(border=True):
            if card.get("image_url"):
                st.image(card["image_url"], use_container_width=True)
            else:
                st.caption("No image available")

            detail = html.escape(_set_label(card) or card.get("type_line", ""))
            extra = f"${card['price_usd']:.2f}" if card.get("price_usd") else ""
            st.markdown(
                f"<div class='owned-name' title='{html.escape(card['name'])}'>{html.escape(card['name'])}</div>"
                f"<div class='owned-meta' title='{detail}'>{detail or '&nbsp;'}</div>"
                + (f"<div class='owned-meta'>{extra or '&nbsp;'}</div>" if has_prices else ""),
                unsafe_allow_html=True,
            )

            minus_col, qty_col, plus_col = st.columns(3, vertical_alignment="center")
            with minus_col:
                if st.button("−", key=f"own_minus_{card_id}", use_container_width=True):
                    _change_qty(card_id, card["qty"] - 1)
            with qty_col:
                st.markdown(f"<div class='owned-qty'>× {card['qty']}</div>", unsafe_allow_html=True)
            with plus_col:
                if st.button("+", key=f"own_plus_{card_id}", use_container_width=True):
                    _change_qty(card_id, card["qty"] + 1)

            if st.button("Remove", key=f"own_remove_{card_id}", use_container_width=True):
                _change_qty(card_id, 0)

if total_pages > 1:
    prev_col, label_col, next_col = st.columns([1, 2, 1])
    with prev_col:
        if st.button("◀ Prev", disabled=page <= 1, use_container_width=True, key="collection_prev"):
            st.session_state["collection_page"] = page - 1
            st.rerun()
    with label_col:
        st.markdown(
            f"<div style='text-align: center; line-height: 2.4;'>Page {page} of {total_pages}</div>",
            unsafe_allow_html=True,
        )
    with next_col:
        if st.button("Next ▶", disabled=page >= total_pages, use_container_width=True, key="collection_next"):
            st.session_state["collection_page"] = page + 1
            st.rerun()

# Export in the "qty Name (SET) number" format that Arena and most collection sites import
export_text = "\n".join(
    f"{card['qty']} {card['name']}"
    + (f" ({card['set'].upper()}) {card.get('collector_number', '')}".rstrip() if card.get("set") else "")
    for card in owned
)
st.download_button(
    "Download collection list",
    export_text,
    file_name="collection.txt",
    mime="text/plain",
)
