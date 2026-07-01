"""Generate failure-case heatmap for the mid-term report."""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np

from figures import OUTPUT_DIR, ensure_output_dir


def main() -> None:
    ensure_output_dir()

    bugs = [
        "depth_first_search",
        "hanoi",
        "sieve",
        "detect_cycle",
        "find_first_in_sorted",
        "next_palindrome",
        "possible_change",
        "reverse_linked_list",
        "lis",
        "max_sublist_sum",
    ]
    configs = ["Baseline", "MACR", "+Sub-Agent", "+KG", "+Sub+KG"]

    # 0 = fail/no patch, 1 = generated but not plausible, 2 = plausible pass
    data = np.array(
        [
            [0, 2, 2, 2, 2],  # depth_first_search
            [0, 2, 2, 2, 2],  # hanoi
            [0, 2, 2, 2, 2],  # sieve
            [2, 0, 2, 2, 2],  # detect_cycle
            [2, 0, 0, 2, 2],  # find_first_in_sorted
            [2, 0, 2, 2, 2],  # next_palindrome
            [2, 0, 2, 2, 2],  # possible_change
            [2, 0, 2, 2, 0],  # reverse_linked_list
            [2, 2, 0, 2, 2],  # lis
            [1, 1, 1, 1, 1],  # max_sublist_sum
        ]
    )

    fig, ax = plt.subplots(figsize=(8, 6))
    cmap = mcolors.ListedColormap(["#EF5350", "#FFCA28", "#66BB6A"])
    im = ax.imshow(data, cmap=cmap, aspect="auto", vmin=0, vmax=2)

    ax.set_xticks(np.arange(len(configs)))
    ax.set_yticks(np.arange(len(bugs)))
    ax.set_xticklabels(configs)
    ax.set_yticklabels(bugs, fontsize=9)

    labels = {0: "F", 1: "G", 2: "P"}
    for i in range(len(bugs)):
        for j in range(len(configs)):
            text = labels[data[i, j]]
            ax.text(j, i, text, ha="center", va="center", fontsize=12)

    ax.set_title("Failure Case Heatmap Across Configurations")
    fig.colorbar(im, ax=ax, ticks=[0.33, 1, 1.66], label="Status")
    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "report_failure_heatmap.pdf")
    fig.savefig(out_path, bbox_inches="tight", dpi=300)
    plt.close(fig)
    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
