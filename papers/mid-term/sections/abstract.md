# Abstract

Automated Program Repair (APR) aims to reduce the cost of software debugging by automatically generating patches for buggy programs.
Recent Large Language Models (LLMs) have shown promising results in patch generation, yet they still struggle with long-context reasoning, context pollution, and precise dependency understanding in real-world codebases.
This paper proposes MACR, a Multi-Agent Collaborative Repair framework that orchestrates specialized sub-agents for fault localization, patch generation, and validation, while leveraging a dynamic code knowledge graph built from Abstract Syntax Trees to provide structured code context.
We evaluate MACR on the QuixBugs dataset and demonstrate that collaborative agent orchestration combined with code knowledge graphs improves repair effectiveness compared to single-agent baselines.
Our results highlight the importance of role specialization and structured context in LLM-based program repair.
