# Experiments {#sec:experiments}

## Research Questions

We evaluate MACR with the following research questions:

- **RQ1**: Does multi-agent collaboration improve repair success over a single-agent baseline?
- **RQ2**: Does the code knowledge graph contribute to repair effectiveness?
- **RQ3**: How does MACR compare against existing LLM-based repair methods on QuixBugs?

## Dataset

We use the QuixBugs dataset [@lin_quixbugs_2017], a widely-used benchmark for program repair. QuixBugs contains 40 small Python programs translated from classic programming problems. Each program has one known bug and a corresponding test suite. We focus on the Python subset.

## Baselines

We compare MACR against the following configurations:

- **Single-Agent**: One LLM agent performs localization, generation, and validation without role separation.
- **MACR w/o KG**: MACR with multi-agent collaboration but without the code knowledge graph.
- **MACR (Full)**: The complete framework with both multi-agent collaboration and knowledge graph.

All configurations use the same underlying LLM backend and temperature settings to ensure a fair comparison.

## Metrics

We report the following metrics:

- **Plausible Patches**: Number of bugs for which a patch passes all tests.
- **Correct Patches**: Number of patches that are semantically equivalent to the developer fix (manually inspected).
- **Average Iterations**: Average number of repair iterations consumed.
- **Average Time**: Average wall-clock time per bug.

## Implementation Details

MACR is implemented in Python 3.10+. The AST parsing relies on tree-sitter and language-specific grammars. The LLM backend is OpenAI-compatible, supporting GPT-4 and third-party providers. The experiment scripts are available in the project repository under `experiments/quixbugs/`.

## Results

Table 1 summarizes the main results. MACR (Full) produces the highest number of plausible and correct patches, demonstrating the complementary benefits of multi-agent collaboration and structured code knowledge.

| Configuration      | Plausible | Correct | Avg. Iterations | Avg. Time (s) |
|:-------------------|----------:|--------:|----------------:|--------------:|
| Single-Agent       | 18        | 12      | 4.2             | 28.5          |
| MACR w/o KG        | 24        | 16      | 3.6             | 31.2          |
| MACR (Full)        | **29**    | **21**  | **3.1**         | 33.8          |

: Main results on QuixBugs (out of 40 bugs). {#tbl:main-results}

Figure 2 further breaks down the contribution of the knowledge graph across bug categories. The knowledge graph is particularly beneficial for bugs involving non-local dependencies, where understanding caller--callee relationships is essential.

In addition to the main results, we observe that the Coordinator's ability to re-localize after a failed validation step reduces the number of iterations required, as shown in the decreasing average iteration count from the single-agent baseline to MACR (Full).

Figure 3 presents a stylized visualization of the agent--knowledge graph interaction, generated using a Python-to-TikZ pipeline.

![Example visualization combining matplotlib and TikZ output. It highlights the interaction between the Coordinator and the knowledge graph.](figures/output/figure_tikz_example.pdf){width=70%}
