# Methodology {#sec:methodology}

## Overview

MACR follows a coordinator--sub-agent architecture. Given a buggy program and a test suite, the **Coordinator** analyzes the task, dispatches specialized sub-agents, and aggregates their outputs until a plausible patch is generated and validated. The framework comprises three core components:

1. **Coordinator Agent**: Plans the repair workflow, selects sub-agents, and manages shared state.
2. **Sub-Agents**: Specialized agents for fault localization, patch generation, and validation.
3. **Code Knowledge Graph**: A dynamic graph built from ASTs that captures code structure and dependencies.

Figure 1 illustrates the overall workflow.

![MACR framework architecture. The Coordinator dispatches Localization, Generation, and Validation agents, which query the Code Knowledge Graph for structured context.](figures/output/figure_architecture.pdf){width=90%}

## Coordinator Agent

The Coordinator receives a repair task and executes a reasoning-acting loop inspired by Self-Debugging [@chen_teaching_2023] and Reflexion [@shinn_reflexion_2023]. At each step, it decides which sub-agent to invoke based on the current state. The decision space includes:

- **Localize**: Identify suspicious functions or statements.
- **Generate**: Produce candidate patches for a given location.
- **Validate**: Run tests and report pass/fail status.
- **Terminate**: Return the best patch or report failure.

By centralizing control, the Coordinator ensures that each sub-agent operates on a focused context, reducing context pollution.

## Sub-Agents

### Fault Localization Agent

The Fault Localization Agent narrows down the search space by ranking program elements according to suspiciousness. It combines spectrum-based fault localization (SBFL) with structural cues from the code knowledge graph, such as caller--callee relationships and data dependencies.

### Patch Generation Agent

Given a localized buggy region, the Patch Generation Agent prompts an LLM to produce candidate patches. The prompt includes:

- The buggy code snippet,
- Surrounding context retrieved from the knowledge graph,
- Failing test messages,
- Examples of similar fixes (optional, retrieved from a patch bank).

### Validation Agent

The Validation Agent compiles and executes the test suite against each candidate patch. It returns a structured report including compilation status, test outcomes, and runtime errors. Patches that pass all tests are considered candidate repairs.

## Code Knowledge Graph

The Code Knowledge Graph is constructed from the AST of the target program using tree-sitter. Nodes represent program entities (functions, classes, variables, imports), and edges represent relationships such as:

- `CALLS`: function invocation,
- `DEFINES`: variable definition,
- `USES`: variable usage,
- `CONTAINS`: hierarchical nesting,
- `IMPORTS`: module dependency.

The graph is updated incrementally as patches are applied, enabling agents to reason about the impact of changes. Figure 2 shows the contribution of the knowledge graph in our ablation study.

![Ablation study results on QuixBugs. KG+Multi-Agent (MACR) outperforms single-agent and no-KG variants.](figures/output/figure_ablation.pdf){width=80%}

## Workflow Example

Algorithm 1 summarizes the MACR repair workflow. The Coordinator iterates until a patch passes all tests or a maximum iteration count is reached.

```pseudocode
# Algorithm: MACR Repair Workflow
Input:  Buggy program P, test suite T, max iterations K
Output: Patch p or failure

G ← BuildKnowledgeGraph(P)
for k = 1 to K do
    L ← LocalizeAgent(P, T, G)
    C ← GenerationAgent(P, L, T, G)
    for each candidate c in C do
        status ← ValidationAgent(P, c, T)
        if status == PASS then
            return c  # patch p
        end if
    end for
    G ← UpdateKnowledgeGraph(G, best candidate)
end for
return failure
```

The iterative nature of MACR allows it to refine localization and generation based on validation feedback, mimicking the debugging process of human developers.
