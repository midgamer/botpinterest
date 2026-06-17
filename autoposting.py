from io import BytesIO
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

CHART_DIR = Path("app/images/charts")


class ChartBuilder:
    def __init__(self):
        CHART_DIR.mkdir(parents=True, exist_ok=True)
        plt.rcParams["figure.facecolor"] = "#1a1a2e"
        plt.rcParams["axes.facecolor"] = "#16213e"
        plt.rcParams["axes.edgecolor"] = "#e94560"
        plt.rcParams["axes.labelcolor"] = "white"
        plt.rcParams["text.color"] = "white"
        plt.rcParams["xtick.color"] = "white"
        plt.rcParams["ytick.color"] = "white"
        plt.rcParams["legend.facecolor"] = "#16213e"
        plt.rcParams["legend.edgecolor"] = "#e94560"

    def create_metrics_chart(self, data: list[dict], filename: str = "metrics.png") -> str:
        df = pd.DataFrame(data)
        if df.empty:
            return ""
        df["date"] = pd.to_datetime(df["date"])

        fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
        fig.suptitle("Pinterest Analytics", fontsize=16, fontweight="bold")

        axes[0].plot(df["date"], df["impressions"], color="#e94560", linewidth=2, marker="o")
        axes[0].fill_between(df["date"], df["impressions"], alpha=0.3, color="#e94560")
        axes[0].set_ylabel("Impressions")
        axes[0].grid(True, alpha=0.3)

        axes[1].plot(df["date"], df["saves"], color="#0f3460", linewidth=2, marker="o")
        axes[1].fill_between(df["date"], df["saves"], alpha=0.3, color="#0f3460")
        axes[1].set_ylabel("Saves")
        axes[1].grid(True, alpha=0.3)

        axes[2].plot(df["date"], df["clicks"], color="#16a085", linewidth=2, marker="o")
        axes[2].fill_between(df["date"], df["clicks"], alpha=0.3, color="#16a085")
        axes[2].set_ylabel("Clicks")
        axes[2].grid(True, alpha=0.3)

        plt.xticks(rotation=45)
        plt.tight_layout()

        filepath = CHART_DIR / filename
        fig.savefig(filepath, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return str(filepath)

    def create_category_pie(self, data: dict[str, int], filename: str = "categories.png") -> str:
        fig, ax = plt.subplots(figsize=(8, 8))
        colors = ["#e94560", "#0f3460", "#16a085", "#f39c12", "#9b59b6", "#1abc9c"]
        wedges, texts, autotexts = ax.pie(
            data.values(),
            labels=data.keys(),
            autopct="%1.1f%%",
            colors=colors[: len(data)],
            startangle=90,
            textprops={"color": "white"},
        )
        ax.set_title("Content Categories Distribution", fontsize=14, fontweight="bold")

        filepath = CHART_DIR / filename
        fig.savefig(filepath, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return str(filepath)
