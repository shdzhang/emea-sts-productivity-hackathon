#!/usr/bin/env python3
"""Generate STS success story consumption chart with engagement period visualization."""

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.patches import FancyBboxPatch

COLORS = {
    "background": "#F5F0E8",
    "line_primary": "#FF3621",
    "line_secondary": "#1B3139",
    "engagement_band": "#FFB30040",
    "engagement_border": "#FFB300",
    "avg_pre": "#888888",
    "avg_post": "#FF3621",
    "text": "#1A1A1A",
    "grid": "#D4CFC5",
    "annotation_bg": "#FFFFFF",
}


def load_data(input_path: str | None) -> dict:
    if input_path:
        return json.loads(Path(input_path).read_text())
    return json.load(sys.stdin)


def build_chart(data: dict, output_path: str, title_override: str | None = None, secondary_metric_key: str | None = None):
    account = data.get("account_name", "")
    asq = data.get("asq_name", "")
    support_type = data.get("support_type", "")
    metric_label = data.get("metric_label", "$DBUs")
    eng_start = data.get("engagement_start_month", 0)
    eng_end = data.get("engagement_end_month", 0)
    points = data.get("data", [])

    if not points:
        print("Error: no data points provided", file=sys.stderr)
        sys.exit(1)

    points = [p for p in points if p.get("value") is not None]
    if not points:
        print("Error: no non-null data points", file=sys.stderr)
        sys.exit(1)

    months = [p["month"] for p in points]
    values = [p["value"] for p in points]

    pre_vals = [p["value"] for p in points if p["month"] < eng_start]
    post_vals = [p["value"] for p in points if p["month"] > eng_end]
    pre_avg = sum(pre_vals) / len(pre_vals) if pre_vals else 0
    post_avg = sum(post_vals) / len(post_vals) if post_vals else 0
    growth_pct = ((post_avg - pre_avg) / pre_avg * 100) if pre_avg > 0 else 0

    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    fig.patch.set_facecolor(COLORS["background"])
    ax.set_facecolor(COLORS["background"])

    ax.axvspan(eng_start, eng_end, alpha=0.25, color=COLORS["engagement_border"], label="STS Engagement", zorder=1)
    ax.axvline(eng_start, color=COLORS["engagement_border"], linestyle="--", linewidth=0.8, alpha=0.6)
    ax.axvline(eng_end, color=COLORS["engagement_border"], linestyle="--", linewidth=0.8, alpha=0.6)

    if pre_vals:
        pre_months = [p["month"] for p in points if p["month"] < eng_start]
        ax.hlines(pre_avg, min(months), eng_start, colors=COLORS["avg_pre"], linestyles="dashed", linewidth=1.2, label=f"Pre-avg: ${pre_avg:,.0f}")
    if post_vals:
        post_months = [p["month"] for p in points if p["month"] > eng_end]
        ax.hlines(post_avg, eng_end, max(months), colors=COLORS["avg_post"], linestyles="dashed", linewidth=1.2, label=f"Post-avg: ${post_avg:,.0f}")

    ax.plot(months, values, color=COLORS["line_primary"], linewidth=2.5, marker="o", markersize=4, zorder=3, label=metric_label)

    if secondary_metric_key and "secondary_data" in data:
        sec_points = data["secondary_data"]
        sec_months = [p["month"] for p in sec_points]
        sec_values = [p["value"] for p in sec_points]
        sec_label = data.get("secondary_metric_label", "Secondary")
        ax.plot(sec_months, sec_values, color=COLORS["line_secondary"], linewidth=1.8, marker="s", markersize=3, linestyle="--", zorder=2, label=sec_label)

    if post_avg > 0 and pre_avg > 0:
        arrow_x = eng_end + (max(months) - eng_end) * 0.5
        sign = "+" if growth_pct >= 0 else ""
        ax.annotate(
            f"{sign}{growth_pct:.0f}%",
            xy=(arrow_x, post_avg),
            fontsize=14,
            fontweight="bold",
            color=COLORS["avg_post"] if growth_pct >= 0 else COLORS["text"],
            ha="center",
            va="bottom",
            bbox=dict(boxstyle="round,pad=0.3", facecolor=COLORS["annotation_bg"], edgecolor=COLORS["engagement_border"], alpha=0.9),
        )

    mid_eng = (eng_start + eng_end) / 2
    y_range = max(values) - min(values) if values else 1
    ax.text(mid_eng, max(values) + y_range * 0.05, "STS\nEngagement", ha="center", va="bottom", fontsize=8, color=COLORS["engagement_border"], fontweight="bold")

    chart_title = title_override or f"{account} — {support_type} ({asq})"
    ax.set_title(chart_title, fontsize=13, fontweight="bold", color=COLORS["text"], pad=15)
    ax.set_xlabel("Months Relative to ASQ Creation", fontsize=10, color=COLORS["text"])
    ax.set_ylabel(f"{metric_label} ($/month)", fontsize=10, color=COLORS["text"])

    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.grid(True, alpha=0.3, color=COLORS["grid"])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(COLORS["grid"])
    ax.spines["bottom"].set_color(COLORS["grid"])

    ax.legend(loc="upper left", fontsize=8, framealpha=0.9)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=COLORS["background"])
    plt.close(fig)
    print(f"Chart saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate STS success story consumption chart")
    parser.add_argument("--input", help="Path to JSON input file (default: stdin)")
    parser.add_argument("--output", required=True, help="Output PNG file path")
    parser.add_argument("--title", help="Override chart title")
    parser.add_argument("--secondary-metric", help="Key for secondary metric overlay")
    args = parser.parse_args()

    data = load_data(args.input)
    build_chart(data, args.output, title_override=args.title, secondary_metric_key=args.secondary_metric)


if __name__ == "__main__":
    main()
