# SoftwareEngineering-DeltaWhaleSharks-Project

## Run locally

1. Install dependencies: `python3 -m pip install -r requirements.txt`

## Import cards from Scryfall

Set `MONGODB_URI` in your local `.env` file, then run:

```sh
python3 get_card_data.py
```

The importer streams Scryfall's Default Cards bulk dataset into
`Magic_Cards.Cards`, keeping the first 5,000 records with `lang == "en"`
in bulk-file order. Change `CARD_LIMIT` in `get_card_data.py` to adjust this limit.
The limit applies per run; existing documents are not deleted, so the collection
may contain more than 5,000 cards after earlier imports. Each printing
(including alternate sets and artwork) is a separate document with the full
Scryfall fields, including image URLs; images themselves are not downloaded.
It writes in batches of 500 and uses a unique index on Scryfall's `id` field.
Rerunning updates existing cards without duplicating them or deleting local
fields. It does not remove cards absent from a later download.

An existing collection must have unique Scryfall `id` values before importing.
The download is large and may take several minutes. If interrupted, rerun the
same command; completed batches remain saved.

## Ask Rocky about imported cards

Set `ROCKY_API_KEY` in `.env`, then run `python3 rocky.py`.

Type `exit`, `quit` or `leave` to finish the conversation.

The script retrieves the available Rocky model automatically through the 
`/v1/models` endpoint and uses it to answer questions through the 
`/v1/responses` endpoint.

The script queries `Magic_Cards.Cards` using MongoDB filters defined in
`rocky.py`. By default, it selects up to 5 English card printings that are 
legal in Modern, are red creatures, and have a mana value (`cmc`) of 3 or 
less. Results are sorted alphabetically by name.

Only the fields listed in `CARD_FIELDS` are sent to Rocky. Rocky uses this 
data to answer questions about the selected cards. Since the script sends a 
limited sample of cards, its answers may not represent every card in the 
database.

To change which cards are retrieved, edit the `query` dictionary in `rocky.
py`. To change the maximum number of cards retrieved, edit `CARD_LIMIT`.
