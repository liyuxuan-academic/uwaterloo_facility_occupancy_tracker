#!/usr/bin/env python3
"""
Read data/occupancy.csv and generate time-series plots per facility.
Outputs:
  plots/occupancy_today.png  — today's data
  plots/occupancy_week.png   — last 7 days
  plots/occupancy_all.png    — full history
"""

import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "occupancy.csv")
PLOTS_DIR = os.path.join(os.path.dirname(__file__), "plots")
EASTERN = ZoneInfo("America/Toronto")

# Consistent colour per facility
PALETTE = [
    "#1f77b4", "#ff7f0e", "#2ca02c",
    "#d62728", "#9467bd", "#8c564b",
]


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_FILE, parse_dates=["timestamp"])
    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_localize("America/Toronto", ambiguous="infer", nonexistent="shift_forward")
    df = df.sort_values("timestamp")
    return df


def plot_window(df: pd.DataFrame, title: str, filename: str) -> None:
    if df.empty:
        print(f"  Skipping {filename} — no data in window")
        return

    facilities = df["facility"].unique()
    colors = {f: PALETTE[i % len(PALETTE)] for i, f in enumerate(sorted(facilities))}

    fig, ax = plt.subplots(figsize=(12, 6))

    for facility in sorted(facilities):
        fdf = df[df["facility"] == facility].copy()
        ax.plot(
            fdf["timestamp"],
            fdf["current_pct"],
            label=facility.title(),
            color=colors[facility],
            linewidth=1.8,
            marker="o",
            markersize=3,
        )

    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_ylabel("Occupancy (%)", fontsize=11)
    ax.set_xlabel("Time (Eastern)", fontsize=11)
    ax.set_ylim(0, 110)
    ax.axhline(100, color="red", linestyle="--", linewidth=0.8, alpha=0.5, label="Capacity")
    ax.grid(True, alpha=0.3, linestyle="--")

    # Smart x-axis formatting — use AutoDateLocator to avoid tick explosions
    locator = mdates.AutoDateLocator(tz=EASTERN, minticks=3, maxticks=10)
    ax.xaxis.set_major_locator(locator)
    span = df["timestamp"].max() - df["timestamp"].min()
    if span <= timedelta(hours=24):
        fmt = mdates.DateFormatter("%H:%M", tz=EASTERN)
    elif span <= timedelta(days=7):
        fmt = mdates.DateFormatter("%a %H:%M", tz=EASTERN)
    else:
        fmt = mdates.DateFormatter("%b %d", tz=EASTERN)
    ax.xaxis.set_major_formatter(fmt)

    plt.xticks(rotation=30, ha="right")
    ax.legend(loc="upper right", fontsize=8, ncol=2)

    fig.tight_layout()
    os.makedirs(PLOTS_DIR, exist_ok=True)
    path = os.path.join(PLOTS_DIR, filename)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {path}")


def main():
    if not os.path.isfile(DATA_FILE):
        print(f"Data file not found: {DATA_FILE}")
        return

    df = load_data()
    now = df["timestamp"].max()

    print(f"Loaded {len(df)} rows, {df['facility'].nunique()} facilities")
    print(f"Range: {df['timestamp'].min()} → {now}")

    # Today only
    today_start = now.normalize()
    plot_window(
        df[df["timestamp"] >= today_start],
        f"Facility Occupancy — Today ({today_start.strftime('%b %d, %Y')})",
        "occupancy_today.png",
    )

    # Last 7 days
    week_start = now - timedelta(days=7)
    plot_window(
        df[df["timestamp"] >= week_start],
        "Facility Occupancy — Last 7 Days",
        "occupancy_week.png",
    )

    # All time
    plot_window(df, "Facility Occupancy — All Time", "occupancy_all.png")


if __name__ == "__main__":
    main()
