"""Generate the ablation results bar chart for the mid-term report."""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from figures import OUTPUT_DIR, ensure_output_dir


def main() -> None:
    ensure_output_dir()

    configs = [
        "Baseline",
        "MACR",
        "MACR +\nSub-Agent",
        "MACR + KG",
        "MACR +\nSub-Agent + KG",
    ]
    plausible = [87.5, 80.0, 90.0, 95.0, 90.0]
    generated = [92.5, 85.0, 95.0, 100.0, 97.5]

    x = np.arange(len(configs))
    width = 0.35

    fig, ax = plt.subplots(figsize=(9, 5))
    bars1 = ax.bar(x - width / 2, plausible, width, label="Plausible Rate (%)", color="#42A5F5")
    bars2 = ax.bar(x + width / 2, generated, width, label="Patch Generation Rate (%)", color="#66BB6A")

    ax.set_ylabel("Rate (%)")
    ax.set_title("Ablation Results on QuixBugs Python (N = 40)")
    ax.set_xticks(x)
    ax.set_xticklabels(configs, fontsize=9)
    ax.legend()
    ax.set_ylim(0, 110)
    ax.axhline(y=87.5, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)

    for bar in bars1 + bars2:
        height = bar.get_height()
        ax.annotate(
            f"{height:.1f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "report_results.pdf")
    fig.savefig(out_path, bbox_inches="tight", dpi=300)
    plt.close(fig)
    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
