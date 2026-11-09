"""LangChain pipeline for building MTG decks via JSON MongoDB queries."""

from itertools import zip_longest
import json
import os
import re
from dotenv import load_dotenv
from langchain_core.runnables import RunnableLambda

from database import get_cards_collection
from rocky import ask_rocky_json, get_model

load_dotenv()

FORMATS = {"standard", "modern", "commander", "pioneer", "legacy", "vintage", "pauper"}
BASIC_LANDS = {"W": "Plains", "U": "Island", "B": "Swamp", "R": "Mountain", "G": "Forest"}

CARD_FIELDS = {
    "_id": 0,
    "id": 1,
    "name": 1,
    "mana_cost": 1,
    "cmc": 1,
    "type_line": 1,
    "oracle_text": 1,
    "color_identity": 1,
    "image_uris": 1,
    "card_faces": 1,
    "legalities": 1,
    "edhrec_rank": 1,
    "penny_rank": 1,
}

ALLOWED_FIELDS = {
    "name", "oracle_text", "type_line", "cmc", "color_identity", "colors",
    "mana_cost", "keywords", "power", "toughness", "loyalty", "rarity",
    "edhrec_rank", "penny_rank",
    "card_faces.oracle_text", "card_faces.type_line",
}
ALLOWED_OPERATORS = {
    "$and", "$or", "$not", "$nor", "$in", "$nin", "$all", "$elemMatch",
    "$eq", "$ne", "$lt", "$lte", "$gt", "$gte", "$regex", "$options", "$exists",
}
FORBIDDEN_OPERATORS = {"$where", "$function", "$accumulator", "$expr"}


def normalize_colors(colors):
    """Normalize color strings like 'blue-black', 'Dimir', or 'U, B' into ['B', 'U']."""
    aliases = {
        "white": "W", "blue": "U", "black": "B", "red": "R", "green": "G", "colorless": "",
        "azorius": "WU", "dimir": "UB", "rakdos": "BR", "gruul": "RG", "selesnya": "GW",
        "orzhov": "WB", "izzet": "UR", "golgari": "BG", "boros": "RW", "simic": "GU",
        "esper": "WUB", "grixis": "UBR", "jund": "BRG", "naya": "RGW", "bant": "GWU",
        "abzan": "WBG", "jeskai": "URW", "sultai": "BGU", "mardu": "RWB", "temur": "GUR",
        "wubrg": "WUBRG", "five-color": "WUBRG", "5c": "WUBRG",
    }
    tokens = re.split(r"[, /-]+", colors.lower()) if isinstance(colors, str) else (colors or [])
    result = set()
    for token in tokens:
        if not isinstance(token, str):
            raise ValueError("Colors must be names or W, U, B, R, G.")
        if token.lower() in {"and", "", "c"}:
            continue
        mapped = aliases.get(token.lower(), token.upper())
        if any(c not in "WUBRG" for c in mapped):
            raise ValueError("Use color names or W, U, B, R, G.")
        result.update(mapped)
    return sorted(result)


def validate_filter(mongo_filter, depth=0, in_operator=False):
    """Ensure the LLM's MongoDB filter contains no unsafe operators and strip unknown fields."""
    if depth > 6 or not isinstance(mongo_filter, dict) or not mongo_filter:
        raise ValueError("Invalid MongoDB filter from LLM.")
    cleaned = {}
    for key, val in mongo_filter.items():
        if key in FORBIDDEN_OPERATORS:
            raise ValueError(f"Unsupported MongoDB field or operator: {key}")
        allowed = (ALLOWED_OPERATORS - {"$and", "$or", "$nor"}) if in_operator else (ALLOWED_FIELDS | {"$and", "$or", "$nor"})
        if key not in allowed:
            if key.startswith("$"):
                raise ValueError(f"Unsupported MongoDB field or operator: {key}")
            continue
        if key in {"$and", "$or", "$nor"}:
            if not isinstance(val, list) or not val:
                raise ValueError(f"{key} requires a non-empty list.")
            sub_items = [validate_filter(item, depth + 1) for item in val if isinstance(item, dict)]
            if sub_items:
                cleaned[key] = sub_items
        elif isinstance(val, dict):
            cleaned[key] = validate_filter(val, depth + 1, in_operator=True)
        elif isinstance(val, list):
            if key not in {"$in", "$nin", "$all", "color_identity", "colors", "keywords"}:
                raise ValueError(f"Unexpected list for {key}.")
            cleaned[key] = val
        elif isinstance(val, (str, int, float)) and not isinstance(val, bool):
            cleaned[key] = val
        elif isinstance(val, bool) and key == "$exists":
            cleaned[key] = val
        else:
            raise ValueError(f"Invalid filter value for {key}.")
    return cleaned


def build_base_filter(deck_format, colors):
    """Enforce English cards, format legality, and color identity in Python."""
    legality = {"$in": ["legal", "restricted"]} if deck_format == "vintage" else "legal"
    base = {
        "lang": "en",
        f"legalities.{deck_format}": legality,
    }
    if colors is not None:
        base["color_identity"] = {"$not": {"$elemMatch": {"$nin": colors}}}
        if colors and deck_format != "commander":
            base["colors"] = {"$in": colors}
    return base


def _popularity_rank(card):
    """Return a combined popularity rank using edhrec_rank and penny_rank (lower = more popular)."""
    ranks = [
        r for r in (card.get("edhrec_rank"), card.get("penny_rank"))
        if isinstance(r, (int, float)) and not isinstance(r, bool) and r > 0
    ]
    return min(ranks) if ranks else 999999


def run_mongo_query(mongo_filter, base_filter, limit=35):
    """Run a validated MongoDB filter, deduplicate by name, and prioritize popular meta cards."""
    safe_filter = validate_filter(mongo_filter)
    combined = {"$and": [base_filter, safe_filter]} if safe_filter else base_filter
    cursor = (
        get_cards_collection()
        .find(combined, CARD_FIELDS)
        .limit(limit * 5)
    )
    unique = {}
    for card in cursor:
        name = card.get("name")
        if not name or "Basic" in card.get("type_line", ""):
            continue
        if name not in unique or _popularity_rank(card) < _popularity_rank(unique[name]):
            unique[name] = card
    ranked_cards = sorted(unique.values(), key=_popularity_rank)
    return ranked_cards[:limit]


# ---------------------------------------------------------------------------
# LangChain Pipeline Steps
# ---------------------------------------------------------------------------

def _infer_colors_from_prompt(text):
    """Infer MTG colors from color names, guild/shard aliases, or color-pie mechanics in the prompt."""
    lower = text.lower()
    explicit = []
    for word in re.findall(r"[a-z0-9-]+", lower):
        if word in {
            "white", "blue", "black", "red", "green", "colorless",
            "azorius", "dimir", "rakdos", "gruul", "selesnya",
            "orzhov", "izzet", "golgari", "boros", "simic",
            "esper", "grixis", "jund", "naya", "bant",
            "abzan", "jeskai", "sultai", "mardu", "temur", "wubrg", "5c",
        }:
            explicit.append(word)
    if explicit:
        return normalize_colors(" ".join(explicit))

    color_keywords = {
        "W": ("lifegain", "gain life", "angel", "soldier", "cat", "vigilance", "indestructible", "exile target", "tax", "stax"),
        "U": ("counterspell", "counter target", "draw", "blink", "flicker", "return", "flying", "wizard", "merfolk", "mill", "bounce", "control", "hate", "annoy", "frustrate", "lock", "unfun"),
        "B": ("sacrifice", "dies", "graveyard", "destroy", "discard", "zombie", "vampire", "demon", "deathtouch", "reanimate", "lose life", "hate", "annoy", "punish", "miserable", "cruel", "suffering", "toxic"),
        "R": ("burn", "damage", "steal", "gain control", "threaten", "haste", "goblin", "dragon", "prowess", "treasure", "aggro"),
        "G": ("ramp", "mana", "land", "forest", "elf", "elves", "trample", "dinosaur", "hydra", "beast", "+1/+1 counter", "fight"),
    }
    scores = {c: sum(1 for kw in kws if kw in lower) for c, kws in color_keywords.items()}
    matched = [c for c, score in sorted(scores.items(), key=lambda x: -x[1]) if score > 0][:2]
    return sorted(matched) if matched else ["U", "B"]


def _plan_searches(state):
    """Step 1: Break the user's request into colors and 2 distinct search sub-goals."""
    if state.get("progress"):
        state["progress"]("Breaking strategy into search steps…")

    colors = state["colors"] if state["colors"] is not None else _infer_colors_from_prompt(state["question"])
    lower_q = state["question"].lower()

    parts = [
        p.strip()
        for p in re.split(r"\b(?:and then|and also|while also|and|with|plus|then)\b|[,;]", state["question"], flags=re.IGNORECASE)
        if len(p.strip()) >= 6
    ]
    if len(parts) >= 2:
        searches = [parts[0], " and ".join(parts[1:3])]
    elif any(w in lower_q for w in ("hate", "annoy", "miserable", "frustrate", "punish", "unfun", "rage")):
        searches = [
            "counter target spell or return target permanent to hand",
            "target opponent discards a card or sacrifices a creature or loses life",
        ]
    else:
        searches = [
            f"core engine cards for: {state['question']}",
            f"synergy and payoff cards for: {state['question']}",
        ]

    return {
        **state,
        "colors": colors,
        "strategy_summary": state["question"],
        "searches": searches[:2],
    }


def _generate_and_run_single_search(goal, deck_format, colors, base_filter, model, headers):
    """Reusable sub-chain: LLM outputs {"query": ..., "output": <Mongo filter>} -> run in MongoDB."""
    prompt = (
        f"Search goal: {goal}\n"
        "Return ONLY JSON with a 1-sentence 'query' and a MongoDB regex 'output' on oracle_text using 2-3 short MTG rules phrases separated by |:\n"
        '{"query": "Searching for cards that ...", "output": {"oracle_text": {"$regex": "phrase1|phrase2", "$options": "i"}}}'
    )
    parsed = ask_rocky_json(prompt, model, headers, max_completion_tokens=6144)
    mongo_query = parsed["output"]
    try:
        cards = run_mongo_query(mongo_query, base_filter, limit=30)
        # If the LLM combined multiple fields and got too few matches, retry with just oracle_text
        if len(cards) < 5 and isinstance(mongo_query, dict) and "oracle_text" in mongo_query and len(mongo_query) > 1:
            cards = run_mongo_query({"oracle_text": mongo_query["oracle_text"]}, base_filter, limit=30)
        # If a long multi-word regex phrase still matched fewer than 5 cards, broaden it to key MTG terms
        if len(cards) < 5 and isinstance(mongo_query, dict):
            raw_regex = (mongo_query.get("oracle_text") or {}).get("$regex", "") if isinstance(mongo_query.get("oracle_text"), dict) else ""
            words = [w for w in re.findall(r"[a-zA-Z]{4,}", raw_regex.lower()) if w not in {"this", "that", "your", "with", "from", "into", "when", "whenever", "creature", "creatures", "target", "card", "cards", "battlefield"}]
            if words:
                broad_query = {"oracle_text": {"$regex": "|".join(dict.fromkeys(words[:5])), "$options": "i"}}
                cards = run_mongo_query(broad_query, base_filter, limit=30)
    except ValueError:
        cards = []
    return {"log": parsed["query"], "query": mongo_query, "cards": cards}


def _execute_searches(state):
    """Step 2: Run the query generator chain for each search goal and interleave results."""
    base_filter = build_base_filter(state["format"], state["colors"])
    search_batches = []
    search_logs = []

    single_search_chain = RunnableLambda(
        lambda goal: _generate_and_run_single_search(
            goal, state["format"], state["colors"], base_filter, state["model"], state["headers"]
        )
    )

    for goal in state["searches"]:
        if state.get("progress"):
            state["progress"](f"Searching database for: {goal}")
        try:
            result = single_search_chain.invoke(goal)
            search_logs.append(result["log"])
            if result["cards"]:
                search_batches.append(result["cards"])
        except (ValueError, RuntimeError):
            continue

    # Interleave results across all searches so every requested theme gets equal representation
    combined_cards = {}
    for group in zip_longest(*search_batches):
        for card in group:
            if card and card["name"] not in combined_cards:
                combined_cards[card["name"]] = card

    # Fallback: if regex searches returned fewer cards than needed, pull additional popular legal cards in color
    target_nonlands = 62 if state["format"] == "commander" else 9
    if len(combined_cards) < target_nonlands:
        fallback_cursor = (
            get_cards_collection()
            .find(base_filter, CARD_FIELDS)
            .limit(300)
        )
        fallback_pool = []
        for card in fallback_cursor:
            name = card.get("name")
            if name and "Basic" not in card.get("type_line", "") and name not in combined_cards:
                fallback_pool.append(card)
        for card in sorted(fallback_pool, key=_popularity_rank):
            if card["name"] not in combined_cards:
                combined_cards[card["name"]] = card
                if len(combined_cards) >= max(target_nonlands, 40):
                    break

    if not combined_cards:
        raise ValueError("No matching cards found in the database for this format and color combination.")

    return {
        **state,
        "base_filter": base_filter,
        "search_logs": search_logs,
        "candidates": list(combined_cards.values()),
    }


def _infer_card_role(card):
    """Derive a concise deck role label from a card's oracle text and type line."""
    text = (card.get("oracle_text") or "").lower()
    front_type = card.get("type_line", "Spell").split("//")[0].split("—")[0].strip() or "Spell"
    if "gain" in text and "life" in text:
        return "Lifegain synergy"
    if "lose" in text and "life" in text:
        return "Life drain"
    if "deals" in text and "damage" in text:
        return "Direct damage"
    if "counter target" in text:
        return "Counterspell"
    if "destroy target" in text or "exile target" in text:
        return "Removal"
    if "search your library for a" in text and "land" in text or "add {" in text:
        return "Mana acceleration"
    if "draw a card" in text or "draw two" in text or "draw cards" in text:
        return "Card advantage"
    if "sacrifice a" in text:
        return "Sacrifice synergy"
    if "enters" in text:
        return "Enter trigger"
    return f"{front_type} synergy"


def _select_cards_with_llm(state):
    """Step 3: Pass combined search results to the LLM to choose deck cards, quantities, and land count."""
    if state.get("progress"):
        state["progress"]("Selecting cards and assembling the deck…")

    is_commander = state["format"] == "commander"
    max_copies = 1 if is_commander else 4
    default_lands = 37 if is_commander else 23

    pool_limit = 22 if is_commander else 16
    candidate_lines = [
        f"- {c['name']} ({c.get('mana_cost', '')}, {c.get('type_line', '').split('—')[0].strip()}): {(c.get('oracle_text') or '').replace(chr(10), ' ')[:55]}"
        for c in state["candidates"][:pool_limit]
    ]

    commander_rule = (
        "Pick 1 legendary creature commander first, then pick the best fitting cards (qty 1)."
        if is_commander
        else f"Pick the 10 best fitting cards from Candidates using qty 3 or {max_copies} for each card."
    )

    prompt = (
        f"Request ({state['format']}): {state['question']}\n"
        "Candidates (ordered by popularity):\n"
        + "\n".join(candidate_lines)
        + "\n\n"
        f"{commander_rule} "
        "Do not count total deck size; Python fills remaining slots and lands automatically.\n"
        "Return ONLY JSON:\n"
        f'{{"query": "1-2 sentence explanation of how the deck works", "output": {{"land_count": {default_lands}, "cards": [{{"name": "Exact Name from Candidates", "qty": {max_copies}, "role": "2-4 word role"}}]}}}}\n'
    )

    response = ask_rocky_json(prompt, state["model"], state["headers"], max_completion_tokens=6144)
    output = response["output"] if isinstance(response["output"], dict) else {}
    return {
        **state,
        "strategy_explanation": response["query"],
        "requested_land_count": output.get("land_count"),
        "raw_selections": output.get("cards", []),
    }


def _cleanup_and_add_lands(state):
    """Step 4: Verify selected card names, respect chosen quantities, and fill Basic Lands by mana symbols."""
    is_commander = state["format"] == "commander"
    deck_size = 100 if is_commander else 60
    default_lands = 37 if is_commander else 24
    max_copies = 1 if is_commander else 4

    raw_lands = state.get("requested_land_count")
    try:
        target_lands = int(raw_lands)
        if is_commander:
            target_lands = max(30, min(45, target_lands))
        else:
            target_lands = max(16, min(30, target_lands))
    except (ValueError, TypeError):
        target_lands = default_lands

    target_spells = deck_size - target_lands
    by_name = {}
    for c in state["candidates"]:
        full_lower = c["name"].lower()
        by_name[full_lower] = c
        if "//" in full_lower:
            for face in full_lower.split("//"):
                face_key = face.strip()
                if face_key and face_key not in by_name:
                    by_name[face_key] = c

    cleaned = []
    seen = set()
    current_spells = 0

    for item in state.get("raw_selections", []):
        if not isinstance(item, dict):
            continue
        raw_name = str(item.get("name", "")).strip()
        card = by_name.get(raw_name.lower())
        if not card or card["name"] in seen:
            continue
        try:
            qty = int(item.get("qty", 1))
        except (ValueError, TypeError):
            qty = 1
        is_land = "Land" in card.get("type_line", "")
        remaining_slots = (deck_size - sum(c["qty"] for c in cleaned)) if is_land else (target_spells - current_spells)
        qty = max(1, min(qty, max_copies, remaining_slots))
        if qty <= 0 or remaining_slots <= 0:
            continue
        rank = _popularity_rank(card)
        cleaned.append({
            "name": card["name"],
            "qty": qty,
            "role": str(item.get("role", "land" if is_land else "spell")),
            "popularity_rank": rank if rank < 999999 else None,
            "image_uris": card.get("image_uris"),
            "card_faces": card.get("card_faces"),
        })
        seen.add(card["name"])
        if not is_land:
            current_spells += qty
        if current_spells >= target_spells:
            break

    # Top up from remaining retrieved candidates only if the deck needs more nonland cards
    for card in state["candidates"]:
        if current_spells >= target_spells:
            break
        if "Land" in card.get("type_line", "") or card["name"] in seen:
            continue
        qty = min(max_copies, target_spells - current_spells)
        rank = _popularity_rank(card)
        cleaned.append({
            "name": card["name"],
            "qty": qty,
            "role": _infer_card_role(card),
            "popularity_rank": rank if rank < 999999 else None,
            "image_uris": card.get("image_uris"),
            "card_faces": card.get("card_faces"),
        })
        seen.add(card["name"])
        current_spells += qty

    # Allocate Basic Lands proportional to the colored mana symbols in the chosen cards
    colors = state["colors"]
    land_names = [BASIC_LANDS[c] for c in colors if c in BASIC_LANDS] or ["Wastes"]
    lands_needed = max(0, deck_size - sum(c["qty"] for c in cleaned))

    if lands_needed > 0:
        pip_weights = {BASIC_LANDS[c]: 1 for c in colors if c in BASIC_LANDS}
        for entry in cleaned:
            card_doc = by_name.get(entry["name"].lower(), {})
            mana_cost = card_doc.get("mana_cost", "")
            for c in colors:
                if c in BASIC_LANDS:
                    pip_weights[BASIC_LANDS[c]] += mana_cost.count(c) * entry["qty"]

        total_weight = sum(pip_weights.values()) or len(land_names)
        allocated = {}
        remaining = lands_needed
        for i, land_name in enumerate(land_names):
            if i == len(land_names) - 1:
                allocated[land_name] = remaining
            else:
                share = round(lands_needed * (pip_weights.get(land_name, 1) / total_weight))
                share = max(1, min(remaining - (len(land_names) - 1 - i), share))
                allocated[land_name] = share
                remaining -= share

        for land_name, qty in allocated.items():
            if qty > 0:
                cleaned.append({"name": land_name, "qty": qty, "role": "land"})

    return {
        "strategy": state.get("strategy_explanation") or state.get("strategy_summary") or state["question"],
        "search_logs": state.get("search_logs", []),
        "cards": cleaned,
        "format": state["format"],
        "colors": colors,
        "total_cards": sum(c["qty"] for c in cleaned),
    }


def get_recommendations(question, format="modern", colors=None, progress=None):
    """Run the LangChain deck-building chain and return a finished deck."""
    if not isinstance(question, str) or len(question.strip()) < 3:
        raise ValueError("Please describe the deck strategy you want to build.")
    if not isinstance(format, str) or format.lower() not in FORMATS:
        raise ValueError(f"Unsupported format: {format}")

    api_key = os.getenv("ROCKY_API_KEY")
    if not api_key:
        raise RuntimeError("ROCKY_API_KEY is not set in your .env file.")

    headers = {"Authorization": f"Bearer {api_key}"}
    model = get_model(headers)
    explicit_colors = normalize_colors(colors) if (colors is not None and str(colors).strip() != "") else None

    chain = (
        RunnableLambda(_plan_searches)
        | RunnableLambda(_execute_searches)
        | RunnableLambda(_select_cards_with_llm)
        | RunnableLambda(_cleanup_and_add_lands)
    )

    return chain.invoke({
        "question": question.strip(),
        "format": format.lower(),
        "colors": explicit_colors,
        "model": model,
        "headers": headers,
        "progress": progress,
    })
