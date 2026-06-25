# MACR 实验记录

## QuixBugs 消融实验

### 实验配置

| 配置 | 知识图谱 | 子 Agent | 说明 |
|------|----------|----------|------|
| MACR | ✅ | ✅ | 完整框架 |
| MACR − KG | ❌ | ✅ | 仅禁用知识图谱 |
| MACR − Sub-Agents | ✅ | ❌ | 仅禁用子 Agent 协同 |
| Baseline | ❌ | ❌ | 单 Agent 直接修复 |

### 运行命令

```bash
# 完整 40 bug 消融实验
uv run python experiments/quixbugs/run_ablation.py --limit 40 --max-steps 5

# 小批量快速验证（5 bug）
uv run python experiments/quixbugs/run_ablation.py --limit 5 --max-steps 3
```

### 初步结果（limit = 5）

| 配置 | 修复数/总数 | 补丁生成数/总数 | 平均尝试次数 |
|------|-------------|-----------------|--------------|
| MACR | 5/5 | 5/5 | 2.00 |
| MACR − KG | 5/5 | 5/5 | 2.00 |
| MACR − Sub-Agents | 5/5 | 5/5 | 1.00 |
| Baseline | 5/5 | 5/5 | 1.00 |

> 注：前 5 个 bug（bitcount、breadth_first_search、bucketsort、depth_first_search、detect_cycle）较为简单，所有配置均全部通过。完整 40 bug 结果 pending。

### 完整结果（limit = 40）

| 配置 | 修复数/总数 | 补丁生成数/总数 | 平均尝试次数 |
|------|-------------|-----------------|--------------|
| MACR | - / - | - / - | - |
| MACR − KG | - / - | - / - | - |
| MACR − Sub-Agents | - / - | - / - | - |
| Baseline | - / - | - / - | - |

> 注：实际结果请在运行实验后从 `outputs/quixbugs/ablation_summary.json` 中读取并回填。

### 观察与结论

- 待补充。
