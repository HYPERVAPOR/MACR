"""Generate a TikZ-compatible PGF figure using matplotlib.

This script demonstrates how to produce vector graphics that can be embedded
in LaTeX either as PDF or as native PGF/TikZ code.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from figures import OUTPUT_DIR, ensure_output_dir


def main() -> None:
    ensure_output_dir()

    # Save a standard PDF version
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot([0, 1, 2, 3, 4], [0, 1, 4, 9, 16], "o-", label="$y = x^2$")
    ax.plot([0, 1, 2, 3, 4], [0, 1, 2, 3, 4], "s--", label="$y = x$")
    ax.set_xlabel("Input $x$")
    ax.set_ylabel("Output $y$")
    ax.set_title("Example Plot with Matplotlib + LaTeX Labels")
    ax.legend()
    ax.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()

    pdf_path = os.path.join(OUTPUT_DIR, "figure_tikz_example.pdf")
    fig.savefig(pdf_path, bbox_inches="tight", dpi=300)
    print(f"Saved {pdf_path}")

    # Save a PGF version for native TikZ embedding
    matplotlib.use("pgf")
    fig2, ax2 = plt.subplots(figsize=(6, 3))
    ax2.plot([0, 1, 2, 3, 4], [0, 1, 4, 9, 16], "o-", label="$y = x^2$")
    ax2.plot([0, 1, 2, 3, 4], [0, 1, 2, 3, 4], "s--", label="$y = x$")
    ax2.set_xlabel("Input $x$")
    ax2.set_ylabel("Output $y$")
    ax2.set_title("Example Plot with Matplotlib + LaTeX Labels")
    ax2.legend()
    ax2.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()

    pgf_path = os.path.join(OUTPUT_DIR, "figure_tikz_example.pgf")
    fig2.savefig(pgf_path, bbox_inches="tight", dpi=300)
    print(f"Saved {pgf_path}")

    plt.close("all")


if __name__ == "__main__":
    main()
