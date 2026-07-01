# Introduction

Software bugs are inevitable and expensive. Automated Program Repair (APR) seeks to alleviate this burden by automatically suggesting or applying patches to buggy code. Early APR techniques, such as GenProg [@le_goues_genprog_2012] and semantics-based approaches [@nguyen_semfix_2013], relied on genetic programming and code mutation. While pioneering, these methods often produced low-quality patches and struggled to scale to large codebases [@kim_automatic_2013].

The emergence of Large Language Models (LLMs) has reinvigorated APR research. Models such as GPT-4 have demonstrated remarkable code understanding and generation capabilities, enabling end-to-end patch generation from natural-language bug descriptions or failing tests [@xia_practical_2023; @yang_survey_2025]. However, LLM-based repair faces several challenges:

1. **Context pollution**: Feeding the entire codebase into a single prompt dilutes the model's attention and introduces irrelevant information [@zhang_llm_2025].
2. **Role entanglement**: A single agent must simultaneously localize faults, design patches, and verify correctness, leading to sub-optimal reasoning [@chen_teaching_2023].
3. **Dependency blindness**: LLMs operate on flat token sequences and may miss structural dependencies critical for correct patching [@xue_exploring_2025].

To address these issues, we propose **MACR** (Multi-Agent Collaborative Repair), a framework that decomposes the repair workflow into specialized sub-agents coordinated by a central orchestrator. MACR further constructs a dynamic **code knowledge graph** from Abstract Syntax Trees (ASTs) to provide agents with precise structural and dependency context. Our contributions are:

- A multi-agent orchestration architecture for APR with dynamic role assignment and context isolation.
- A code knowledge graph module that extracts AST-based dependencies to support fault localization and patch validation.
- An empirical evaluation on QuixBugs [@lin_quixbugs_2017] showing improved repair success over single-agent and ablation baselines.

The remainder of this paper is organized as follows. Section 2 reviews related work. Section 3 describes the MACR framework. Section 4 presents the experimental setup and results. Section 5 concludes and outlines future work.
