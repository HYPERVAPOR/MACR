# 三、方法论

## 3.1 总体架构

MACR 的总体架构如图\ref{fig:architecture} 所示，核心是一个统一协调器与若干专业化子智能体。协调器负责解析输入、维护全局状态、调度子智能体，并通过共享黑板（blackboard）与动态代码知识图谱实现信息共享。该设计与多智能体系统综述中强调的角色专业化、状态共享与迭代反馈原则一致 [@li_survey_2024]。

![MACR 总体架构](figures/output/figure_architecture.pdf){#fig:architecture width=80%}

与传统单智能体 APR 相比，MACR 具有以下特点：

- **任务解耦**：将定位、生成、验证与诊断分离，降低单一提示的复杂度。
- **结构化上下文**：通过代码知识图谱显式表达程序结构，弥补 LLM 对长程依赖的不足。
- **迭代反馈**：验证失败信息经诊断智能体分析后，以结构化形式反馈给生成智能体。

## 3.2 协调器：动态任务编排

协调器是 MACR 的中枢。其工作流程如下：

1. **接收输入**：bug 报告、缺陷代码仓库与测试套件。
2. **初始化知识图谱**：调用 KG Agent 对代码仓库进行静态分析，构建初始代码 KG。
3. **故障定位**：调用 Fault Localization Agent，生成可疑语句排名。
4. **循环修复**：
   a. 调用 Patch Generation Agent 生成候选补丁。
   b. 调用 Validation Agent 执行编译与测试。
   c. 若通过所有测试，则返回补丁。
   d. 若失败，调用 Diagnosis Agent 分析失败原因，并更新 KG 与生成策略。
5. **终止条件**：达到最大迭代次数或修复成功。

该流程借鉴了 RepairAgent 的自主决策循环，但将其扩展为显式多智能体协作 [@bouzenia_repairagent_2024]。

$$\text{Coordinator}(R, T, B): \text{patch or } \bot$$

其中 $R$ 为代码仓库，$T$ 为测试套件，$B$ 为 bug 报告。

## 3.3 故障定位智能体

故障定位智能体采用 SBFL 技术，结合测试执行覆盖信息计算每条语句的可疑度。具体地，采用 Tarantula 公式：

$$
\text{Susp}(s) = \frac{\frac{n_{ef}(s)}{n_e}}{\frac{n_{ef}(s)}{n_e} + \frac{n_{nf}(s)}{n_n}}
$$

其中 $n_{ef}$ 为执行语句 $s$ 的失败测试数，$n_e$ 为总失败测试数，$n_{nf}$ 为执行语句 $s$ 的通过测试数，$n_n$ 为总通过测试数。SBFL 因其轻量、无需额外标注而被广泛应用于 APR 流水线中 [@le_goues_genprog_2012]。

在 MACR 中，故障定位结果不仅作为补丁生成的候选位置，还被输入 KG Agent 用于增强可疑节点的上下文表示。

## 3.4 补丁生成智能体

补丁生成智能体接收协调器提供的以下输入：

- 可疑语句列表 $S = \{(s_i, \text{Susp}(s_i))\}$
- 相关代码上下文 $C(s_i)$（来自 KG 的局部子图）
- 历史失败信息 $H$（由 Diagnosis Agent 提供）

生成过程可形式化为：

$$
P = \text{LLM}_{\text{gen}}\bigl(s^*, C(s^*), H, \text{prompt}\bigr)
$$

其中 $s^*$ 为排名最高的可疑语句。为了提升生成质量，我们采用了 Self-Debugging 中的思路，在提示中加入执行反馈与代码解释要求，以引导模型进行更审慎的推理 [@chen_teaching_2023]。

## 3.5 验证智能体

验证智能体负责编译补丁并执行测试套件，返回结果 $V = (\text{compile\_ok}, \text{passed}, \text{failed}, \text{trace})$。与单智能体 APR 不同，MACR 的验证结果不仅用于判断补丁正确性，还被结构化后输入 Diagnosis Agent，用于指导下一轮生成。

## 3.6 诊断智能体

当补丁未通过测试时，诊断智能体执行以下任务：

1. 对比失败测试的执行轨迹与预期行为。
2. 识别补丁引入的新错误或未覆盖的边界条件。
3. 生成针对下一轮生成的改进建议 $F$。

诊断智能体可被视为 MACR 的“反思”模块，类似于 Reflexion 中利用言语强化学习进行自我改进的机制 [@shinn_reflexion_2023]。不同之处在于，MACR 的反思不仅依赖自然语言总结，还结合代码 KG 中的结构信息进行根因定位。

## 3.7 代码知识图谱

代码知识图谱是 MACR 的核心创新之一。它通过 AST 静态分析提取以下节点与关系：

- **节点类型**：函数（Function）、类（Class）、变量（Variable）、控制流节点（ControlFlow）、测试（Test）等。
- **关系类型**：调用（CALLS）、包含（CONTAINS）、依赖（DEPENDS\_ON）、修改（MODIFIES）等。

KG 的节点评分函数综合考虑可疑度与结构中心性：

$$
\text{Score}(n) = \alpha \cdot \text{Susp}(n) + \beta \cdot \text{Centrality}(n) + \gamma \cdot \text{Relevance}(n, q)
$$

其中 $q$ 为 bug 报告中的关键词，$\alpha, \beta, \gamma$ 为可配置权重。

代码知识图谱在多智能体环境中的作用已得到相关研究支持。例如，Zuo 等人提出的 KG4Diagnosis 框架利用多智能体协作与知识图谱实现复杂系统故障诊断，验证了结构化知识对智能体推理的促进作用 [@zuo_kg4diagnosis_2025]。SciAgents 则展示了如何将科学知识编码为知识图谱，并由多智能体进行自主发现与推理 [@ghafarollahi_sciagents_2025]。

## 3.8 多轮迭代策略

MACR 通过迭代逐步逼近正确补丁。设第 $t$ 轮的状态为 $X_t = (S_t, H_t, G_t)$，其中 $G_t$ 为当前代码 KG。状态转移为：

$$
X_{t+1} = f(X_t, P_t, V_t, F_t)
$$

其中 $P_t$ 为第 $t$ 轮生成的补丁，$V_t$ 为验证结果，$F_t$ 为诊断反馈。迭代持续至补丁通过测试或达到最大轮次 $T_{\max}$。

与 AutoGen 等通用 MAS 框架相比，MACR 的状态转移是领域专用的：针对 APR 任务定义了明确的状态空间与动作空间，避免了通用框架中因过度自由而导致的任务偏离问题 [@li_survey_2024]。
