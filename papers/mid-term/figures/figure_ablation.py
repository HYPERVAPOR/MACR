"""Generate the ablation study bar chart."""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from figures import OUTPUT_DIR, ensure_output_dir


def main() -> None:
    ensure_output_dir()

    configs = ["Single-Agent", "MACR w/o KG", "MACR (Full)"]
    plausible = [18, 24, 29]
    correct = [12, 16, 21]

    x = np.arange(len(configs))
    width = 0.35

    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars1 = ax.bar(x - width / 2, plausible, width, label="Plausible", color="#42A5F5")
    bars2 = ax.bar(x + width / 2, correct, width, label="Correct", color="#66BB6A")

    ax.set_ylabel("Number of Bugs (out of 40)")
    ax.set_title("Ablation Study on QuixBugs")
    ax.set_xticks(x)
    ax.set_xticklabels(configs)
    ax.legend()
    ax.set_ylim(0, 35)

    for bar in bars1 + bars2:
        height = bar.get_height()
        ax.annotate(
            f"{int(height)}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "figure_ablation.pdf")
    fig.savefig(out_path, bbox_inches="tight", dpi=300)
    plt.close(fig)
    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
