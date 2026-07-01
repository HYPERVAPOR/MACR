"""Generate token consumption vs. success rate chart for the report."""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

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
    tokens = [176.4, 171.5, 312.4, 196.2, 285.2]  # in thousands
    plausible = [87.5, 80.0, 90.0, 95.0, 90.0]
    efficiency = [p / t for p, t in zip(plausible, tokens)]

    fig, ax1 = plt.subplots(figsize=(9, 5))

    color1 = "#EF5350"
    ax1.set_xlabel("Configuration")
    ax1.set_ylabel("Total Tokens (K)", color=color1)
    bars = ax1.bar(configs, tokens, color=color1, alpha=0.7, label="Total Tokens (K)")
    ax1.tick_params(axis="y", labelcolor=color1)
    ax1.set_ylim(0, 360)

    for bar, t in zip(bars, tokens):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 5,
            f"{t:.1f}K",
            ha="center",
            va="bottom",
            fontsize=8,
            color=color1,
        )

    ax2 = ax1.twinx()
    color2 = "#5C6BC0"
    ax2.set_ylabel("Plausible Rate (%)", color=color2)
    ax2.plot(configs, plausible, color=color2, marker="o", linewidth=2, markersize=8, label="Plausible Rate (%)")
    ax2.tick_params(axis="y", labelcolor=color2)
    ax2.set_ylim(70, 100)

    # Efficiency annotations
    for i, (cfg, eff) in enumerate(zip(configs, efficiency)):
        ax2.annotate(
            f"η={eff:.2f}",
            xy=(i, plausible[i]),
            xytext=(0, 10),
            textcoords="offset points",
            ha="center",
            fontsize=7,
            color="#333",
        )

    ax1.set_title("Token Consumption vs. Plausible Rate on QuixBugs")
    fig.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "report_tokens.pdf")
    fig.savefig(out_path, bbox_inches="tight", dpi=300)
    plt.close(fig)
    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
