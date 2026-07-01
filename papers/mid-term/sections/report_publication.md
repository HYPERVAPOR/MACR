# 四、论文发表情况

## 4.1 论文选题与目标会议

本研究的核心贡献在于提出了面向自动化程序修复的多智能体协同框架 MACR，并通过代码知识图谱增强了智能体的结构化推理能力。结合当前软件工程领域的研究热点，论文计划投稿至以下顶级会议：

- **ICSE 2026**（IEEE/ACM International Conference on Software Engineering）：软件工程领域最具影响力的综合性会议，重点关注软件工程方法与工具创新。
- **FSE 2026**（ACM SIGSOFT International Symposium on Software Testing and Analysis）：聚焦软件测试与分析，APR 是其传统热点方向。

## 4.2 论文主要贡献

论文计划提出以下四点贡献：

1. **MACR 框架**：首个将动态角色编排、迭代诊断反馈与代码知识图谱结合的 LLM-based APR 框架。
2. **面向 APR 的多智能体协同协议**：设计了协调器驱动的任务分解、执行与反馈机制，避免了通用 MAS 框架在专用任务上的角色漂移问题。
3. **代码知识图谱增强的修复流程**：通过 AST 构建动态 KG，为各子智能体提供结构化的代码上下文。
4. **QuixBugs 系统评估**：实验表明 MACR 在 QuixBugs 上达到 55% 的修复率，并通过消融实验验证了多智能体分工与 KG 的有效性。

## 4.3 论文结构与进度

论文初稿结构如下：

| 章节 | 内容 | 进度 |
|------|------|------|
| 1. Introduction | 研究背景、问题、贡献 | 已完成 |
| 2. Background | APR 与 MAS 基础 | 已完成 |
| 3. Related Work | 传统 APR、LLM APR、Agentic APR | 已完成 |
| 4. Methodology | MACR 框架详细设计 | 已完成 |
| 5. Evaluation | QuixBugs 实验与消融分析 | 已完成 |
| 6. Discussion | 失败模式、局限与未来工作 | 初稿 |
| 7. Conclusion | 总结 | 初稿 |

: 论文各章节进度 {#tab:paper-progress}

表\ref{tab:paper-progress} 显示了论文各章节的当前进度。

| 会议 | 截稿日期（预计） | 投稿计划 |
|------|-----------------|---------|
| ICSE 2026 | 2025 年 12 月 | 目标投稿 |
| FSE 2026 | 2026 年 2 月 | 备选投稿 |

: 目标会议投稿计划 {#tab:submission-plan}

表\ref{tab:submission-plan} 列出了目标会议与投稿计划。

## 4.4 现有支撑成果

项目前期已在工具实现与数据集建设方面取得阶段性成果，并已形成可运行的 MACR 原型系统。相关代码与实验结果已整理至 `src/macr/`、`tests/` 与 `outputs/quixbugs/` 目录，为论文的复现提供了基础。
