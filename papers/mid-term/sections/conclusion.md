# Conclusion and Future Work {#sec:conclusion}

We presented MACR, a multi-agent collaborative repair framework that combines dynamic role orchestration with a code knowledge graph for automated program repair. By delegating localization, generation, and validation to specialized sub-agents, MACR reduces context pollution and improves repair focus. The integration of an AST-based knowledge graph further enhances dependency-aware reasoning. Our evaluation on QuixBugs shows that MACR outperforms single-agent and ablation baselines in terms of both plausible and correct patches.

Future work will extend MACR in several directions:

1. **Larger benchmarks**: Evaluate MACR on Defects4J [@just_defects4j_2014] and SWE-bench to assess scalability to real-world projects.
2. **Fine-grained agent roles**: Introduce additional specialized agents for test generation, patch ranking, and explanation.
3. **Learning from feedback**: Train or fine-tune the Coordinator's dispatch policy using reinforcement learning on historical repair traces.
4. **Multi-language support**: Extend the AST parser and templates to Java, C, and other languages.

We believe that structured collaboration among specialized agents is a promising path toward practical LLM-based program repair.
