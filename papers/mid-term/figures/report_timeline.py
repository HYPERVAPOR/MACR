"""Generate Gantt-style timeline for the next-stage research plan."""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from figures import OUTPUT_DIR, ensure_output_dir


def main() -> None:
    ensure_output_dir()

    tasks = [
        ("Hard-bug trace analysis", 0, 2, "#42A5F5"),
        ("KG strategy optimization", 1.5, 2.5, "#66BB6A"),
        ("Sub-Agent trigger redesign", 2, 2.5, "#FFA726"),
        ("Defects4J pilot study", 3, 1.5, "#AB47BC"),
        ("Prompt engineering", 3.5, 1.5, "#EF5350"),
        ("Draft paper writing", 4, 2, "#26C6DA"),
        ("Internal review and revise", 5, 1, "#78909C"),
        ("Submit to ICSE/ESEC-FSE", 6, 0.5, "#8D6E63"),
    ]

    fig, ax = plt.subplots(figsize=(10, 5))
    y_positions = range(len(tasks))

    for i, (name, start, duration, color) in enumerate(tasks):
        ax.barh(i, duration, left=start, height=0.5, color=color, edgecolor="black", linewidth=0.5)
        ax.text(start + duration / 2, i, name, ha="center", va="center", fontsize=8, color="white", weight="bold")

    ax.set_yticks(y_positions)
    ax.set_yticklabels([f"Task {i+1}" for i in range(len(tasks))], fontsize=9)
    ax.set_xlabel("Weeks from 2026-07-01")
    ax.set_title("Next-Stage Research and Paper Writing Timeline")
    ax.set_xlim(0, 7)
    ax.invert_yaxis()
    ax.grid(axis="x", linestyle=":", alpha=0.6)

    # Milestones
    milestones = [
        (2, "Optimization complete"),
        (4.5, "Defects4J results"),
        (6, "Submission ready"),
    ]
    for x, label in milestones:
        ax.axvline(x=x, color="red", linestyle="--", linewidth=1, alpha=0.7)
        ax.text(x, len(tasks) - 0.3, label, rotation=90, va="top", ha="center", fontsize=8, color="red")

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "report_timeline.pdf")
    fig.savefig(out_path, bbox_inches="tight", dpi=300)
    plt.close(fig)
    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
