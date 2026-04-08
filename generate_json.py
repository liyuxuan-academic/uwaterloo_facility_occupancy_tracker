#!/usr/bin/env python3
"""
Convert data/occupancy.csv → docs/data.json for the GitHub Pages dashboard.
Groups data by facility, keeping the last 30 days.
"""

import json
import os
from datetime import datetime, timedelta

import pandas as pd

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "occupancy.csv")
OUT_FILE = os.path.join(os.path.dirname(__file__), "docs", "data.json")
KEEP_DAYS = 30


def main():
    if not os.path.isfile(DATA_FILE):
        print(f"Data file not found: {DATA_FILE}")
        return

    df = pd.read_csv(DATA_FILE, parse_dates=["timestamp"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Keep last N days
    cutoff = df["timestamp"].max() - timedelta(days=KEEP_DAYS)
    df = df[df["timestamp"] >= cutoff].copy()
    df = df.sort_values("timestamp")

    # Build per-facility series
    facilities = {}
    for facility, group in df.groupby("facility"):
        facilities[facility] = [
            {
                "t": row["timestamp"].strftime("%Y-%m-%dT%H:%M"),
                "pct": int(row["current_pct"]) if pd.notna(row["current_pct"]) else None,
                "count": int(row["current_count"]) if pd.notna(row["current_count"]) else None,
                "max": int(row["max_occupancy"]) if pd.notna(row["max_occupancy"]) else None,
            }
            for _, row in group.iterrows()
        ]

    out = {
        "last_updated": df["timestamp"].max().strftime("%Y-%m-%d %H:%M"),
        "facilities": facilities,
    }

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w") as f:
        json.dump(out, f, separators=(",", ":"))

    total_points = sum(len(v) for v in facilities.values())
    print(f"Wrote {OUT_FILE}: {len(facilities)} facilities, {total_points} data points")


if __name__ == "__main__":
    main()
