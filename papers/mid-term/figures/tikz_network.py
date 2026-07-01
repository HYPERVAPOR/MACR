r"""Generate a standalone TikZ diagram using Python string templating.

This demonstrates the Python + TikZ workflow: Python computes coordinates
and writes a .tikz file that can be \input{} into LaTeX documents.
"""

import os

from figures import OUTPUT_DIR, ensure_output_dir


def main() -> None:
    ensure_output_dir()

    nodes = [
        ("Coordinator", 0, 0, "orange!30"),
        ("Localize", -3, -2, "green!20"),
        ("Generate", 0, -2, "blue!20"),
        ("Validate", 3, -2, "red!20"),
        ("KG", 0, -4, "purple!20"),
    ]

    lines = [
        r"\begin{tikzpicture}[node distance=2.5cm, auto, >=stealth']",
        r"  \tikzset{agent/.style={rectangle, rounded corners, draw=black, fill=#4, minimum width=2cm, minimum height=0.8cm, align=center}}",
    ]

    for name, x, y, color in nodes:
        lines.append(f"  \\node[agent={color}] ({name.lower()}) at ({x},{y}) {{{name}}};")

    edges = [
        ("coordinator", "localize", "dispatch"),
        ("coordinator", "generate", "dispatch"),
        ("coordinator", "validate", "dispatch"),
        ("localize", "kg", "query"),
        ("generate", "kg", "query"),
        ("validate", "kg", "update"),
    ]

    for src, dst, label in edges:
        lines.append(
            f"  \\draw[->, thick] ({src}) -- ({dst}) node[midway, fill=white, inner sep=1pt] {{{label}}};"
        )

    lines.append(r"\end{tikzpicture}")

    out_path = os.path.join(OUTPUT_DIR, "tikz_network.tikz")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
