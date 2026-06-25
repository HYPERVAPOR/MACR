# MACR 中期答辩 PPT

本目录存放硕士论文中期答辩的 PowerPoint 材料。

## 文件结构

```text
slides/
├── README.md                              # 本说明
└── slides-2026-6-25/
    ├── MACR_中期答辩_2026_06_25.pptx      # 最终答辩 PPT
    ├── generate_ppt.py                    # 自动生成脚本
    └── assets/                            # 图表资源
        ├── chart_success_rates.png
        └── chart_failure_matrix.png
```

## 设计规范

- **风格**：Nature / Science 式国际学术顶刊简洁风
- **主色调**：深普鲁士蓝 `#1A365D`
- **背景色**：浅灰白 `#FAFAFA`
- **点缀色**：铁锈红 `#B7410E`、金黄 `#D4AF37`（仅用于强调）
- **字体**：`Microsoft YaHei`（微软雅黑，Windows 默认无衬线中文字体）
- **排版**：严格网格对齐、大量留白、无全图背景、无过度投影/发光
- **图表**：扁平化、无 3D、无阴影
- **框架图**：矢量圆角矩形 + 1.25 pt 细线边框

## 幻灯片内容

共 28 页，分为 6 个部分：

1. **论文概况**（背景、目标）
2. **研究进展概览**
3. **已完成的核心工作**
   - MACR 总体架构图
   - MACR 工作流程图
   - 形式化定义 / 关键公式
   - ReAct 决策循环图
   - Knowledge Graph 构建流程图
   - Sub-Agent 调用机制图
   - 实验结果表与可视化
4. **存在的问题与困惑**
5. **后续研究计划**
6. **总结与致谢**

## 如何重新生成

```bash
cd /home/hv/projs/MACR
uv run python slides/slides-2026-6-25/generate_ppt.py
```

脚本会自动读取 `outputs/quixbugs/ablation_summary.json` 并重新渲染图表和 PPT。

## 使用前的检查

打开 `MACR_中期答辩_2026_06_25.pptx` 后，请替换标题页的占位信息：

- `汇报人：XXX`
- `导师：XXX 教授`

PPT 已统一使用 `Microsoft YaHei`，在 Windows 上可直接正常显示。如果在 macOS / Linux 上播放时字体缺失，可能会自动替换为系统默认无衬线字体。
