# MACR 阶段性实验报告
**实验时间**：2026-06-24 20:53 ~ 2026-06-25 01:52（约 5 小时）
**数据集**：QuixBugs Python（40 个 bug）
**模型**：SiliconFlow `deepseek-ai/DeepSeek-V4-Flash`
**最大步数**：5

---

## 1. 总体结果
| 配置 | Plausible | Generated | Avg Steps | LLM Calls | Tokens | 主要 Tool 调用 |
|------|-----------|-----------|-----------|-----------|--------|---------------|
| Baseline | 35/40 (87.5%) | 37/40 (92.5%) | 2.08 | 120 | 176,408 | direct_patch=37, run_tests=46 |
| MACR | 32/40 (80.0%) | 34/40 (85.0%) | 2.12 | 121 | 171,464 | run_tests=49, direct_patch=36 |
| MACR + Sub-Agent | 36/40 (90.0%) | 38/40 (95.0%) | 2.70 | 146 | 312,405 | direct_patch=38, run_tests=43, explore=23, generate_patch=4 |
| MACR + KG | 38/40 (95.0%) | 40/40 (100.0%) | 2.23 | 130 | 196,233 | direct_patch=41, run_tests=45, query_kg=3 |
| MACR + Sub-Agent + KG | 36/40 (90.0%) | 39/40 (97.5%) | 2.40 | 136 | 285,216 | direct_patch=40, run_tests=42, explore=13, localize=1 |

## 2. 关键发现
1. **Knowledge Graph 提升最明显**。MACR + KG 达到 **95% plausible** 和 **100% patch 生成率**，是所有配置中最好的。
2. **纯 MACR 反而略低于 Baseline**。说明当前 ReAct 循环和 system prompt 还有优化空间，复杂 loop 不一定比单次 direct_patch 更稳。
3. **Sub-Agent 成本偏高、收益有限**。MACR + Sub-Agent 的 token 消耗接近 MACR + KG 的 **1.6 倍**，但效果不如 KG；平均步数也最高（2.70）。
4. **Sub-Agent + KG 没有继续提升**。说明当前 Sub-Agent 的调用策略（频繁 `explore`）可能引入了噪声，需要重新设计触发条件。

## 3. 各配置失败 bug 列表

### Baseline
- `depth_first_search, hanoi, shortest_path_lengths, sieve, to_base`
- `depth_first_search, hanoi, sieve`

### MACR
- `detect_cycle, find_first_in_sorted, next_palindrome, possible_change, reverse_linked_list, shortest_path_lengths, subsequences, to_base`
- `detect_cycle, find_first_in_sorted, next_palindrome, possible_change, reverse_linked_list, shortest_path_lengths`

### MACR + Sub-Agent
- `find_first_in_sorted, lis, max_sublist_sum, shortest_path_length`
- `find_first_in_sorted, lis`

### MACR + KG
- `max_sublist_sum, mergesort`
- 无

### MACR + Sub-Agent + KG
- `max_sublist_sum, reverse_linked_list, shortest_path_lengths, to_base`
- `reverse_linked_list`

## 4. 跨配置失败矩阵
| Bug | Baseline | MACR | MACR + Sub-Agent | MACR + KG | MACR + Sub-Agent + KG |
|-----|------|------|------|------|------|
| bitcount | ✅ | ✅ | ✅ | ✅ | ✅ |
| breadth_first_search | ✅ | ✅ | ✅ | ✅ | ✅ |
| bucketsort | ✅ | ✅ | ✅ | ✅ | ✅ |
| depth_first_search | ❌ | ✅ | ✅ | ✅ | ✅ |
| detect_cycle | ✅ | ❌ | ✅ | ✅ | ✅ |
| find_first_in_sorted | ✅ | ❌ | ❌ | ✅ | ✅ |
| find_in_sorted | ✅ | ✅ | ✅ | ✅ | ✅ |
| flatten | ✅ | ✅ | ✅ | ✅ | ✅ |
| gcd | ✅ | ✅ | ✅ | ✅ | ✅ |
| get_factors | ✅ | ✅ | ✅ | ✅ | ✅ |
| hanoi | ❌ | ✅ | ✅ | ✅ | ✅ |
| is_valid_parenthesization | ✅ | ✅ | ✅ | ✅ | ✅ |
| kheapsort | ✅ | ✅ | ✅ | ✅ | ✅ |
| knapsack | ✅ | ✅ | ✅ | ✅ | ✅ |
| kth | ✅ | ✅ | ✅ | ✅ | ✅ |
| lcs_length | ✅ | ✅ | ✅ | ✅ | ✅ |
| levenshtein | ✅ | ✅ | ✅ | ✅ | ✅ |
| lis | ✅ | ✅ | ❌ | ✅ | ✅ |
| longest_common_subsequence | ✅ | ✅ | ✅ | ✅ | ✅ |
| max_sublist_sum | ✅ | ✅ | 📝 | 📝 | 📝 |
| mergesort | ✅ | ✅ | ✅ | 📝 | ✅ |
| minimum_spanning_tree | ✅ | ✅ | ✅ | ✅ | ✅ |
| next_palindrome | ✅ | ❌ | ✅ | ✅ | ✅ |
| next_permutation | ✅ | ✅ | ✅ | ✅ | ✅ |
| pascal | ✅ | ✅ | ✅ | ✅ | ✅ |
| possible_change | ✅ | ❌ | ✅ | ✅ | ✅ |
| powerset | ✅ | ✅ | ✅ | ✅ | ✅ |
| quicksort | ✅ | ✅ | ✅ | ✅ | ✅ |
| reverse_linked_list | ✅ | ❌ | ✅ | ✅ | ❌ |
| rpn_eval | ✅ | ✅ | ✅ | ✅ | ✅ |
| shortest_path_length | ✅ | ✅ | 📝 | ✅ | ✅ |
| shortest_path_lengths | 📝 | ❌ | ✅ | ✅ | 📝 |
| shortest_paths | ✅ | ✅ | ✅ | ✅ | ✅ |
| shunting_yard | ✅ | ✅ | ✅ | ✅ | ✅ |
| sieve | ❌ | ✅ | ✅ | ✅ | ✅ |
| sqrt | ✅ | ✅ | ✅ | ✅ | ✅ |
| subsequences | ✅ | 📝 | ✅ | ✅ | ✅ |
| to_base | 📝 | 📝 | ✅ | ✅ | 📝 |
| topological_ordering | ✅ | ✅ | ✅ | ✅ | ✅ |
| wrap | ✅ | ✅ | ✅ | ✅ | ✅ |

图例：✅ 通过测试；📝 生成 patch 但未通过；❌ 未生成 patch。

## 5. 值得重点攻克的硬 bug
- **`max_sublist_sum`**：在 MACR + KG 和 MACR + Sub-Agent + KG 中都失败，可能是 KG 给的依赖信息误导了修复。
- **`find_first_in_sorted`**：MACR 和 MACR + Sub-Agent 都生成不出 patch，但 Baseline 和 MACR + KG 能过，说明 ReAct/Sub-Agent 的上下文组织有问题。
- **`reverse_linked_list`** / **`shortest_path_lengths`** / **`to_base`**：在多个配置中反复失败，属于模型本身的难点，需要看 trace 定位是 patch 格式、测试超时还是逻辑错误。

## 6. 下一步建议
1. **以 MACR + KG 为默认基线**，继续调优 KG 构建和查询策略。
2. **重设计 Sub-Agent 触发条件**：避免默认调用 `explore`，改为只在 test 失败或需要定位时才调用；减少 token 开销。
3. **定点分析硬 bug 的 trace**：优先看 `max_sublist_sum`、`find_first_in_sorted`、`reverse_linked_list` 的 `outputs/traces/events.jsonl`。
4. **优化 ReAct prompt**：纯 MACR 比 Baseline 低，说明 coordinator 的 action 选择或 patch 解析 prompt 需要加强。

---

*报告生成时间：2026-06-25*
*原始数据：`outputs/quixbugs/ablation_summary.json` 与 `outputs/traces/events.jsonl`*
