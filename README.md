# MACR: Multi-Agent Collaborative Repair

MACR 是一个面向自动程序修复（Automated Program Repair, APR）的多智能体协同框架，通过动态角色编排与代码知识图谱提升大语言模型在真实代码库上的修复能力。

## 特性

- **动态角色编排**：主 Agent 派发子 Agent 执行定位、补丁生成、验证等子任务，避免上下文污染。
- **代码知识图谱**：基于 AST 动态构建代码结构图谱，为 Agent 提供精确的依赖追踪。
- **可插拔模块**：子 Agent 协同与知识图谱均可独立开关，便于消融实验。
- **数据集适配**：优先支持 QuixBugs，架构预留 Defects4J / SWE-bench 扩展接口。

## 项目结构

```
MACR/
├── src/macr/           # 核心框架代码
├── experiments/        # 实验脚本
├── tests/              # 单元测试
├── docs/               # 文档
└── outputs/            # 实验结果（运行时生成）
```

## 快速开始

### 1. 安装依赖

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入 OPENAI_API_KEY

# 使用 OpenAI-compatible 第三方 Provider（如 vLLM、Ollama、国内代理）时：
# OPENAI_BASE_URL=https://your-provider.com/v1
# OPENAI_USE_BETA_PARSE=false
```

### 3. 运行 QuixBugs 实验

```bash
# 完整 MACR 框架（知识图谱 + 子 Agent）
python experiments/quixbugs/run_macr.py --limit 5

# 单 Agent Baseline
python experiments/quixbugs/run_baseline.py --limit 5

# 消融实验（4 种配置对比）
python experiments/quixbugs/run_ablation.py --limit 5
```

结果默认保存到 `outputs/quixbugs/`。

### 4. 运行测试

```bash
pytest tests/ -v
ruff check src tests experiments
mypy src/macr
```

## 核心模块

| 模块 | 说明 |
|------|------|
| `macr.llm` | LLM 后端抽象，当前支持 OpenAI-compatible API |
| `macr.agents` | ReAct Coordinator + 可配置 Subagent 编排 |
| `macr.knowledge_graph` | 基于 tree-sitter 的 AST 知识图谱 |
| `macr.datasets` | APR 数据集适配器（QuixBugs） |
| `macr.repair` | 补丁生成、应用与修复流程 |
| `macr.evaluation` | 测试执行与指标统计 |

## 内置 Subagent

框架内置以下可配置 subagent，Coordinator 会根据任务描述自动委派：

| Subagent | 用途 | 允许工具 |
|---|---|---|
| `localize` | 定位 bug 位置 | 无 |
| `generate_patch` | 生成候选补丁 | `direct_patch` |
| `validate_patch` | 验证补丁正确性 | 无 |
| `explore` | 探索代码结构/依赖 | `query_kg` |
| `review` | 代码/补丁审查 | 无 |
| `test_writer` | 生成补充测试用例 | 无 |
| `security_audit` | 安全审计 | 无 |
| `planner` | 制定修复计划 | 无 |

### 自定义 Subagent

在项目根目录创建 `.macr/agents/my-agent.md`：

```markdown
---
name: my_agent
description: Short description used by the coordinator to decide delegation.
model: deepseek-ai/DeepSeek-V4-Flash
tools:
  - query_kg
max_steps: 3
---
Your system prompt here.
```

配置优先级：`.macr/agents/` > `~/.macr/agents/` > 内置 `src/macr/agents/builtins/`。

## Trace 追踪

每次修复运行都会自动记录结构化 trace，方便调试和评估。

```bash
# 默认 JSONL 格式
python experiments/quixbugs/run_single.py bitcount --use-kg --use-sub-agents
# 查看 trace
ls outputs/traces/
# events.jsonl  events 级别日志
# runs.jsonl    run 级别摘要

# 切换到 SQLite 格式
MACR_TRACE_STORE=sqlite python experiments/quixbugs/run_single.py bitcount --use-kg --use-sub-agents
```

环境变量：

| 变量 | 说明 | 默认值 |
|---|---|---|
| `MACR_TRACE_STORE` | 存储后端：`jsonl` 或 `sqlite` | `jsonl` |
| `MACR_TRACE_DIR` | trace 输出目录 | `outputs/traces` |

记录的事件类型：`run_start`、`run_end`、`react_step`、`llm_request`、`llm_response`、`subagent_spawn`、`error`。

## 后续扩展

- [ ] Defects4J 数据集适配
- [ ] SWE-bench 数据集适配
- [ ] Java 程序编译与测试执行
- [ ] 更细粒度的 KG 查询（调用链、数据依赖）
- [ ] Agent 反思与多轮迭代

## 许可证

MIT
