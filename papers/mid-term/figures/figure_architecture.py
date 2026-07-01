"""Generate the MACR architecture figure."""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from figures import OUTPUT_DIR, ensure_output_dir


def draw_box(ax, x, y, w, h, text, color, fontsize=9):
    rect = mpatches.FancyBboxPatch(
        (x - w / 2, y - h / 2),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.05",
        facecolor=color,
        edgecolor="black",
        linewidth=1.2,
    )
    ax.add_patch(rect)
    ax.text(x, y, text, ha="center", va="center", fontsize=fontsize, weight="bold")


def draw_arrow(ax, x1, y1, x2, y2, label="", color="black"):
    ax.annotate(
        "",
        xy=(x2, y2),
        xytext=(x1, y1),
        arrowprops=dict(arrowstyle="->", color=color, lw=1.2),
    )
    if label:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.08, label, ha="center", va="bottom", fontsize=8)


def main() -> None:
    ensure_output_dir()

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 5)
    ax.axis("off")

    # Title
    ax.text(4, 4.7, "MACR Architecture", ha="center", va="center", fontsize=14, weight="bold")

    # Coordinator
    draw_box(ax, 4, 3.5, 2.0, 0.7, "Coordinator\n(ReAct Orchestrator)", "#FFCC80")

    # Sub-agents
    draw_box(ax, 1.5, 2.0, 1.6, 0.7, "Localization\nAgent", "#A5D6A7")
    draw_box(ax, 4.0, 2.0, 1.6, 0.7, "Generation\nAgent", "#90CAF9")
    draw_box(ax, 6.5, 2.0, 1.6, 0.7, "Validation\nAgent", "#EF9A9A")

    # Knowledge graph
    draw_box(ax, 4.0, 0.6, 3.0, 0.7, "Code Knowledge Graph\n(AST-based dependencies)", "#CE93D8")

    # Arrows
    draw_arrow(ax, 4.0, 3.15, 1.5, 2.35, "dispatch")
    draw_arrow(ax, 4.0, 3.15, 4.0, 2.35, "dispatch")
    draw_arrow(ax, 4.0, 3.15, 6.5, 2.35, "dispatch")

    draw_arrow(ax, 1.5, 1.65, 4.0, 0.95, "query", color="#555")
    draw_arrow(ax, 4.0, 1.65, 4.0, 0.95, "query", color="#555")
    draw_arrow(ax, 6.5, 1.65, 4.0, 0.95, "update", color="#555")

    # Feedback loop
    draw_arrow(ax, 6.5, 2.35, 4.0, 3.15, "feedback", color="#1565C0")

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "figure_architecture.pdf")
    fig.savefig(out_path, bbox_inches="tight", dpi=300)
    plt.close(fig)
    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
