"""LangChain pipeline for building MTG decks via JSON MongoDB queries."""

from itertools import zip_longest
import json
import os
import re
from dotenv import load_dotenv
from langchain_core.runnables import RunnableLambda

from database import get_cards_collection
from groq_client import ask_groq_json, get_model

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
    "legalities": 1,
}

ALLOWED_FIELDS = {
    "name", "oracle_text", "type_line", "cmc", "color_identity", "colors",
    "mana_cost", "keywords", "power", "toughness", "loyalty", "rarity",
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
    return base


def run_mongo_query(mongo_filter, base_filter, limit=35):
    """Run a validated MongoDB filter and deduplicate printings by card name."""
    safe_filter = validate_filter(mongo_filter)
    combined = {"$and": [base_filter, safe_filter]} if safe_filter else base_filter
    cursor = (
        get_cards_collection()
        .find(combined, CARD_FIELDS)
        .limit(limit * 2)
    )
    unique = {}
    for card in cursor:
        name = card.get("name")
        if name and "Basic" not in card.get("type_line", "") and name not in unique:
            unique[name] = card
            if len(unique) >= limit:
                break
    return list(unique.values())


# ---------------------------------------------------------------------------
# LangChain Pipeline Steps
# ---------------------------------------------------------------------------

def _plan_searches(state):
    """Step 1: Have the LLM break the user's request into colors and sub-goals."""
    if state.get("progress"):
        state["progress"]("Breaking strategy into search steps…")

    prompt = (
        "You are a Magic: The Gathering deck-building assistant. Analyze the user's request.\n"
        "Return JSON in this exact structure (replace placeholders with actual values):\n"
        '{\n'
        '  "query": "<summary of the overall deck strategy>",\n'
        '  "output": {\n'
        '    "colors": ["<color symbol W, U, B, R, or G>"],\n'
        '    "searches": [\n'
        '      "<distinct search goal 1>",\n'
        '      "<distinct search goal 2>"\n'
        '    ]\n'
        '  }\n'
        '}\n'
        "Guidelines:\n"
        "- Break the user's request into 2 to 4 distinct search goals in 'searches' so each theme, "
        "mechanic, or card role they asked for is searched separately.\n"
        "- If 'supplied_colors' is non-empty, keep those exact colors.\n"
        "- If 'supplied_colors' is empty, infer whichever color(s) from W, U, B, R, G (or [] for colorless) "
        "best match the user's prompt and Magic's color pie (e.g. W=lifegain/tokens/order, "
        "U=counterspells/draw/flying, B=discard/destroy/graveyard, R=haste/direct damage/aggro, G=ramp/big creatures/elves).\n"
        f"Request: {json.dumps({'strategy': state['question'], 'format': state['format'], 'supplied_colors': state['colors']})}"
    )

    response = ask_groq_json(prompt, state["model"], state["headers"])
    output = response["output"]

    if state["colors"] is not None:
        colors = state["colors"]
    else:
        raw_colors = output.get("colors", [])
        colors = normalize_colors(raw_colors) if raw_colors else []

    searches = output.get("searches", [state["question"]])
    if not isinstance(searches, list) or not searches:
        searches = [state["question"]]

    return {
        **state,
        "colors": colors,
        "strategy_summary": response["query"],
        "searches": [str(s) for s in searches[:5]],
    }


def _generate_and_run_single_search(goal, deck_format, colors, base_filter, model, headers):
    """Reusable sub-chain: LLM outputs {"query": ..., "output": <Mongo filter>} -> run in MongoDB."""
    prompt = (
        "Generate a MongoDB filter to find Magic: The Gathering cards for this search goal.\n"
        "Return JSON in this exact structure:\n"
        '{\n'
        '  "query": "<description of what this query searches for>",\n'
        '  "output": <MongoDB filter object>\n'
        '}\n'
        "Rules for 'output':\n"
        "- Must be a MongoDB query dict using fields from: oracle_text, type_line, cmc, name.\n"
        "- Use broad, case-insensitive $regex alternatives separated by | so plenty of matching cards are found "
        '(for example: {"oracle_text": {"$regex": "keyword1|keyword2", "$options": "i"}}).\n'
        "- Do NOT include lang, legalities, or color_identity (Python adds those automatically).\n"
        f"Search goal: {goal}\nFormat: {deck_format}\nColors: {colors}"
    )
    parsed = ask_groq_json(prompt, model, headers)
    mongo_query = parsed["output"]
    try:
        cards = run_mongo_query(mongo_query, base_filter, limit=30)
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
        except ValueError:
            continue

    # Interleave results across all searches so every requested theme gets equal representation
    combined_cards = {}
    for group in zip_longest(*search_batches):
        for card in group:
            if card and card["name"] not in combined_cards:
                combined_cards[card["name"]] = card

    # Fallback: if regex searches returned fewer cards than needed, pull additional legal cards in color
    target_nonlands = 62 if state["format"] == "commander" else 9
    if len(combined_cards) < target_nonlands:
        fallback_cursor = (
            get_cards_collection()
            .find(base_filter, CARD_FIELDS)
            .limit(200)
        )
        for card in fallback_cursor:
            name = card.get("name")
            if name and "Basic" not in card.get("type_line", "") and name not in combined_cards:
                combined_cards[name] = card
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


def _select_cards_with_llm(state):
    """Step 3: Pass combined search results to the LLM to choose deck cards, quantities, and land count."""
    if state.get("progress"):
        state["progress"]("Selecting cards and assembling the deck…")

    is_commander = state["format"] == "commander"
    deck_size = 100 if is_commander else 60
    max_copies = 1 if is_commander else 4

    pool_limit = 70 if is_commander else 45
    compact_pool = [
        {
            "name": c["name"],
            "cost": c.get("mana_cost", ""),
            "type": c.get("type_line", ""),
            "text": (c.get("oracle_text") or "")[:90],
        }
        for c in state["candidates"][:pool_limit]
    ]

    prompt = (
        f"Build a {deck_size}-card {state['format']} Magic: The Gathering deck from the candidate cards below "
        "that fulfills the user's request.\n"
        "Return JSON in this exact structure:\n"
        '{\n'
        '  "query": "<explanation of how the deck works and why these cards fit the user request>",\n'
        '  "output": {\n'
        '    "land_count": <number of lands appropriate for this strategy, e.g. 20-26 for 60-card or 36-38 for commander>,\n'
        '    "cards": [\n'
        f'      {{"name": "<Exact Card Name from candidates>", "qty": <1 to {max_copies}>, "role": "<role in deck>"}}\n'
        '    ]\n'
        '  }\n'
        '}\n'
        "Guidelines:\n"
        f"- Choose varied quantities (1 to {max_copies} copies) that make sense for each card's mana cost and the user's wishes.\n"
        "- Balance the themes requested by the user.\n"
        "- Python will automatically supply Basic Lands to reach the full deck size.\n"
        f"User request: {state['question']}\n"
        f"Candidate cards: {json.dumps(compact_pool)}"
    )

    response = ask_groq_json(prompt, state["model"], state["headers"], max_completion_tokens=4096)
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
    by_name = {c["name"].lower(): c for c in state["candidates"]}
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
        qty = max(1, min(qty, max_copies, deck_size - current_spells))
        if qty <= 0:
            continue
        is_land = "Land" in card.get("type_line", "")
        cleaned.append({
            "name": card["name"],
            "qty": qty,
            "role": str(item.get("role", "land" if is_land else "spell")),
        })
        seen.add(card["name"])
        if not is_land:
            current_spells += qty
        if sum(c["qty"] for c in cleaned) >= target_spells:
            break

    # Top up from remaining retrieved candidates only if the deck needs more nonland cards
    for card in state["candidates"]:
        if sum(c["qty"] for c in cleaned) >= target_spells:
            break
        if "Land" in card.get("type_line", "") or card["name"] in seen:
            continue
        qty = min(max_copies, target_spells - sum(c["qty"] for c in cleaned))
        cleaned.append({"name": card["name"], "qty": qty, "role": "support"})
        seen.add(card["name"])

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

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set in your .env file.")

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
        "model": get_model(),
        "headers": {"Authorization": f"Bearer {api_key}"},
        "progress": progress,
    })
