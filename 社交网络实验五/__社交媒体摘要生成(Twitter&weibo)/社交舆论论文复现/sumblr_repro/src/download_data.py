"""Download the Turkey Earthquake tweets dataset (Kaggle, unauthenticated API).

Dataset: gpreda/turkey-earthquake-tweets
Tweets posted 2023-02-07 .. 2023-02-26 about the 2023 Turkey-Syria earthquake.
Chosen as a public, single-event, timestamped replacement for the Sumblr
paper's private 2012 Twitter crawl (see README for the substitution rationale).
"""
import os
import sys
import zipfile

import requests

from config import DATA_DIR

DATASET = "gpreda/turkey-earthquake-tweets"
URL = f"https://www.kaggle.com/api/v1/datasets/download/{DATASET}"


def main() -> int:
    os.makedirs(DATA_DIR, exist_ok=True)
    zip_path = os.path.join(DATA_DIR, "turkey-earthquake-tweets.zip")
    csv_path = os.path.join(DATA_DIR, "turkey_earthquake_tweets.csv")

    if os.path.exists(csv_path):
        print(f"[download] already present: {csv_path}")
        return 0

    print(f"[download] {URL}")
    with requests.get(URL, stream=True, timeout=300) as r:
        r.raise_for_status()
        total = 0
        with open(zip_path, "wb") as f:
            for chunk in r.iter_content(1 << 16):
                f.write(chunk)
                total += len(chunk)
    print(f"[download] {total} bytes -> {zip_path}")

    with zipfile.ZipFile(zip_path) as z:
        z.extractall(DATA_DIR)
        print(f"[download] extracted: {z.namelist()}")

    if not os.path.exists(csv_path):
        print("[download] ERROR: expected CSV not found after extraction")
        return 1
    print(f"[download] ready: {csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
