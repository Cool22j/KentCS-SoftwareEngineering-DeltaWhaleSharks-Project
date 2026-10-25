# SoftwareEngineering-DeltaWhaleSharks-Project

## Run locally

1. Install dependencies:
   ```sh
   python3 -m pip install -r requirements.txt
   ```

2. Set `MONGODB_URI` and `GROQ_API_KEY` in your local `.env` file.

3. Import English cards from Scryfall into MongoDB (`Magic_Cards.Cards`):
   ```sh
   python3 get_card_data.py --limit 5000
   ```
   *(Omit `--limit` to import the full English Scryfall catalog.)*

4. Run the Streamlit app:
   ```sh
   streamlit run main.py
   ```

## How the LangChain Deck Builder Works

When a user enters a deck request in `app.py`, `recommendation.py` runs a four-step LangChain `RunnableLambda` pipeline:

1. **Plan Searches (`_plan_searches`)**: The LLM breaks the user's strategy into 2–3 sub-goals (for example, searching for control cards and searching for aggro cards) and infers colors if none were specified.
2. **Execute MongoDB Queries (`_execute_searches`)**: For each sub-goal, the LLM outputs a JSON object:
   ```json
   {
     "query": "what the agent is searching for to log",
     "output": { "oracle_text": { "$regex": "counter target", "$options": "i" } }
   }
   ```
   `groq_client.parse_json_response()` parses the JSON using Python's `json` library, validates the filter fields, and queries MongoDB for matching legal cards.
3. **Select Cards (`_select_cards_with_llm`)**: The combined search results are passed to the next step of the chain, where the LLM selects the cards and quantities that fit the strategy.
4. **Cleanup & Land Assembly (`_cleanup_and_add_lands`)**: Python deduplicates the selection, enforces copy limits (4 copies in 60-card formats, 1 copy in Commander), and automatically adds Basic Lands to reach 60 (or 100) cards.

## Run Tests

```sh
.venv/bin/python -m unittest discover -s tests -v
```
