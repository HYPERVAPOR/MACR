# 二、工作进展与阶段性成果

截至目前，项目已完成了总体框架设计、数据集构建、原型系统实现、实验评估以及论文初稿撰写等关键任务。下面从系统构建、实验结果与论文产出三个维度进行总结。

## 2.1 MACR 框架实现

MACR 框架采用协调器-智能体（Coordinator-Agent）架构，由统一协调器负责解析问题、分配任务、管理通信并聚合结果。框架已实现了以下核心模块：

- **Coordinator（协调器）**：负责任务分解、状态跟踪与结果汇总。
- **Fault Localization Agent（故障定位智能体）**：基于 Spectrum-based Fault Localization（SBFL）生成可疑代码位置列表。
- **Patch Generation Agent（补丁生成智能体）**：基于 SBFL 排名与代码上下文生成候选补丁。
- **Validation Agent（验证智能体）**：负责补丁编译、测试执行与结果汇总。
- **Diagnosis Agent（诊断智能体）**：当补丁失败时，分析失败原因并反馈至补丁生成阶段，实现迭代修复。
- **Knowledge Graph Agent（知识图谱智能体）**：动态维护代码知识图谱，提供函数调用、变量作用域与数据依赖等结构化信息。

在实现过程中，框架参考了 RepairAgent 的工作流设计思想，即在接收到 bug 报告后，智能体可自主决定下一步动作，如阅读文件、搜索代码、生成补丁、执行测试等 [@bouzenia_repairagent_2024]。与 RepairAgent 不同，MACR 通过显式的多智能体分工与代码知识图谱，增强了任务的专业化与上下文的结构化表达。

## 2.2 数据集与测试基准

实验采用 QuixBugs 数据集作为主体测试基准。QuixBugs 包含 40 个经典编程问题，每个问题均提供有缺陷实现与对应的单元测试，被广泛用作 APR 方法的快速验证平台 [@lin_quixbugs_2017]。在测试过程中，我们修复了若干测试驱动脚本，使其适配当前 Python 环境与依赖版本，确保评估结果可复现。

## 2.3 主要实验结果

### 2.3.1 整体修复率

在 QuixBugs 数据集上，MACR 原型系统的整体修复率为 55%，即成功修复 22/40 个缺陷。作为对比，经典神经 APR 方法 SequenceR 在相同数据集上的修复率约为 20% [@chen_sequencer_2021]，而近期基于 LLM 对话的 ChatRepair 可达 48%–67%（取决于模型与轮次）[@xia_practical_2023]。

![QuixBugs 数据集上不同 APR 方法的修复率对比](figures/output/report_results.pdf){#fig:results width=80%}

如图\ref{fig:results} 所示，MACR 在 QuixBugs 上的修复率高于传统神经 APR 方法，且与先进 LLM-based APR 方法处于同一水平。这一结果表明，多智能体协同与知识图谱的结合能够在不依赖昂贵微调的前提下，显著提升修复能力。

### 2.3.2 成本分析

LLM-based APR 的成本主要体现为 API token 消耗。图\ref{fig:tokens} 展示了 MACR 在 QuixBugs 各样本上的 token 分布。平均每个 bug 约消耗 35k token，中位数约为 28k。这一成本高于单次生成式 APR，但低于需要大量采样的方法（如生成-验证方法通常需要数百次候选生成）。

![QuixBugs 上各样本的 token 消耗分布](figures/output/report_tokens.pdf){#fig:tokens width=80%}

### 2.3.3 失败模式分析

对 18 个未修复样本的失败原因进行分析，可归纳为以下四类：

- **上下文不足（Context Insufficiency）**：缺陷涉及跨文件依赖或外部库，智能体未能获取充分上下文。
- **生成偏差（Generation Bias）**：模型倾向于生成常见但错误的模式，例如边界条件处理不当。
- **验证反馈失效（Feedback Failure）**：测试失败信息未能有效转化为生成智能体可执行的改进建议。
- **知识图谱覆盖不足（KG Coverage）**：部分动态或反射式代码结构难以被静态 AST 分析覆盖。

图\ref{fig:heatmap} 以热力图形式展示了不同失败模式在各类缺陷中的分布。

![失败模式热力图](figures/output/report_failure_heatmap.pdf){#fig:heatmap width=80%}

### 2.3.4 修复时间线

图\ref{fig:timeline} 展示了 MACR 在典型样本上的迭代修复过程。多数样本可在 3–5 轮迭代内完成修复，表明诊断-反馈机制能够有效引导补丁生成。

![典型样本的修复轮次分布](figures/output/report_timeline.pdf){#fig:timeline width=80%}

## 2.4 论文发表进展

围绕 MACR 框架的设计、实现与评估，课题组已启动论文撰写工作，计划投稿至软件工程领域顶级会议。论文题目暂定为 *"MACR: Multi-Agent Collaborative Repair with Dynamic Role Orchestration and Code Knowledge Graphs"*。目前论文已完成以下部分：

- 引言与相关工作梳理，系统对比了传统 APR、LLM-based APR 与多智能体 APR 三类方法。
- MACR 方法论详细描述，包括协调器算法、智能体定义与知识图谱构建流程。
- QuixBugs 实验结果与分析。
- 初步讨论失败模式与未来改进方向。

论文初稿预计于中期检查后一个月内完成，并投稿至 ICSE 2026 或 FSE 2026 等 CCF-A 类会议。
