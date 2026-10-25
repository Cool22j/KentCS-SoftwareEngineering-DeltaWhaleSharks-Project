import argparse
import gzip
import json
import os
import sys
from contextlib import closing
from pathlib import Path
from urllib.request import Request, urlopen

import ijson
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError


BULK_URL = "https://api.scryfall.com/bulk-data/default_cards"
HEADERS = {
    "User-Agent": "DeltaWhaleSharks-CardImporter/1.0",
    "Accept": "application/json",
}
BATCH_SIZE = 500
CARD_LIMIT = None

def open_download(url):
    return urlopen(Request(url, headers=HEADERS), timeout=120)


def read_bulk_cards(metadata):
    """Stream current gzipped JSON Lines or the legacy JSON array export."""
    if metadata.get("jsonl_download_uri"):
        with open_download(metadata["jsonl_download_uri"]) as response:
            with gzip.GzipFile(fileobj=response) as decompressed:
                for line in decompressed:
                    if line.strip():
                        yield json.loads(line)
    elif metadata.get("download_uri"):
        with open_download(metadata["download_uri"]) as response:
            yield from ijson.items(response, "item", use_float=True)
    else:
        raise ValueError("Scryfall bulk metadata has no supported download URL.")


def import_cards(collection, cards, batch_size=BATCH_SIZE, limit=CARD_LIMIT):
    """Upsert all English printings, or an explicit limited sample."""
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    if limit is not None and limit < 1:
        raise ValueError("limit must be positive")
    pending = []
    imported = 0
    for card in cards:
        if card.get("lang") != "en":
            continue
        pending.append(UpdateOne({"id": card["id"]}, {"$set": card}, upsert=True))
        if len(pending) >= batch_size:
            collection.bulk_write(pending, ordered=False)
            imported += len(pending)
            pending.clear()
            print(f"Imported {imported:,} English printings...", flush=True)
        if limit is not None and imported + len(pending) >= limit:
            break
    if pending:
        collection.bulk_write(pending, ordered=False)
        imported += len(pending)
    return imported


def main():
    parser = argparse.ArgumentParser(description="Import the complete English card catalog.")
    parser.add_argument("--limit", type=int, default=None, help="Optional sample size; omit for the full catalog.")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    if os.getenv("MONGODB_URI"):
        print("Using MONGODB_URI from the process environment; it takes precedence over .env.", flush=True)
    load_dotenv(Path(__file__).with_name(".env"))
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise RuntimeError("MONGODB_URI is not set. Add it to your .env file.")

    with MongoClient(uri, serverSelectionTimeoutMS=10000) as client:
        print("Connecting to MongoDB...", flush=True)
        client.admin.command("ping")
        print("MongoDB connected. Preparing cards collection...", flush=True)
        collection = client["Magic_Cards"]["Cards"]
        collection.create_index("id", unique=True)
        collection.create_index([("lang", 1), ("name", 1)])
        collection.create_index([("lang", 1), ("color_identity", 1)])
        with open_download(BULK_URL) as response:
            metadata = json.load(response)
        print(f"Downloading Scryfall data updated {metadata['updated_at']}...", flush=True)
        with closing(read_bulk_cards(metadata)) as cards:
            count = import_cards(collection, cards, limit=args.limit)
        print(f"Done: imported {count:,} English printings into {collection.full_name}.")


if __name__ == "__main__":
    main()
    
