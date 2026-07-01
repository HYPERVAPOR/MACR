# Related Work {#sec:related-work}

## Traditional Automated Program Repair

Traditional APR techniques can be broadly categorized into generate-and-validate and semantics-based approaches. Generate-and-validate methods, exemplified by GenProg [@le_goues_genprog_2012], search the space of possible patches using genetic programming and test suites to validate candidates. Semantics-based techniques leverage constraint solving and program synthesis to produce patches that are correct by construction [@nguyen_semfix_2013]. Despite significant progress, these approaches often suffer from overfitting to test suites and limited patch diversity [@kim_automatic_2013].

## Learning-Based Program Repair

Learning-based APR employs neural networks to model the distribution of correct code. SequenceR [@chen_sequencer_2021] frames repair as a sequence-to-sequence learning problem, translating buggy code into fixed code. Subsequent work has explored transformer architectures, retrieval-augmented generation, and fine-tuning on bug-fix corpora. These methods improve patch quality but still treat repair as a monolithic generation task.

## LLM-Based Repair

Recent studies have applied LLMs such as Codex, ChatGPT, and open-source alternatives to APR. Xia et al. [@xia_practical_2023] showed that conversational repair can fix a substantial fraction of bugs at low cost. Yang et al. [@yang_survey_2025] surveyed 62 recent LLM-based APR systems and highlighted prompt engineering, fine-tuning, pipeline design, and agentic frameworks as four major paradigms. Nevertheless, most existing approaches rely on a single LLM agent, which limits specialization and scalability [@zhang_llm_2025].

## Multi-Agent Systems for Software Engineering

Multi-agent systems have gained traction in software engineering tasks such as code generation, debugging, and vulnerability detection [@he_llm-based_2025; @li_survey_2024]. By assigning different roles to specialized agents, these systems can decompose complex problems and reduce context pollution. However, their application to APR remains under-explored, particularly in combining agent orchestration with structured code knowledge.

## Knowledge Graphs for Code Understanding

Code knowledge graphs encode structural relationships such as function calls, variable dependencies, and control flow. They have been used for fault localization, code summarization, and vulnerability detection. MACR extends this line of work by dynamically constructing AST-based knowledge graphs and integrating them into the multi-agent repair loop.
