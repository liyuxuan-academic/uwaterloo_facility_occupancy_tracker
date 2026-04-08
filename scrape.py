#!/usr/bin/env python3
"""
Scrape UWaterloo facility occupancy and append to data/occupancy.csv.
Designed to be run periodically (e.g., via GitHub Actions every 15 minutes).
"""

import csv
import os
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

URL = "https://warrior.uwaterloo.ca/FacilityOccupancy"
DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "occupancy.csv")
FIELDNAMES = ["timestamp", "facility", "max_occupancy", "current_pct", "current_count"]

EASTERN = ZoneInfo("America/Toronto")


def fetch_occupancy() -> list[dict]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; facility-monitor/1.0; "
            "+https://github.com/yuxuanli/facility_monitor)"
        )
    }
    resp = requests.get(URL, headers=headers, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    cards = soup.select(".occupancy-card")
    if not cards:
        print("WARNING: No .occupancy-card elements found — page structure may have changed.")
        return []

    now = datetime.now(tz=EASTERN).strftime("%Y-%m-%d %H:%M")
    rows = []
    for card in cards:
        text = card.get_text(separator="\n")

        # Facility name (inside h2 > strong within the header)
        name_el = card.select_one(".occupancy-card-header-line-1 h2")
        name = name_el.get_text(strip=True) if name_el else "Unknown"

        # Max occupancy
        import re
        max_match = re.search(r"Max Occupancy[:\s]+(\d+)", text, re.IGNORECASE)
        max_occ = int(max_match.group(1)) if max_match else None

        # Current occupancy percentage
        pct_match = re.search(r"Current Occupancy\D+(\d+)%", text, re.IGNORECASE)
        current_pct = int(pct_match.group(1)) if pct_match else None

        current_count = round(max_occ * current_pct / 100) if (max_occ and current_pct is not None) else None

        rows.append({
            "timestamp": now,
            "facility": name,
            "max_occupancy": max_occ,
            "current_pct": current_pct,
            "current_count": current_count,
        })

    return rows


def append_to_csv(rows: list[dict]) -> None:
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    file_exists = os.path.isfile(DATA_FILE)
    with open(DATA_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


def main():
    print(f"Fetching {URL} ...")
    rows = fetch_occupancy()
    if not rows:
        print("No data extracted. Exiting.")
        sys.exit(1)

    for r in rows:
        print(f"  {r['facility']}: {r['current_pct']}% ({r['current_count']}/{r['max_occupancy']})")

    append_to_csv(rows)
    print(f"Appended {len(rows)} rows to {DATA_FILE}")


if __name__ == "__main__":
    main()
