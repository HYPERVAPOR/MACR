---
name: localize
description: |
  Invoke a specialized localization subagent to identify the likely buggy lines or logic.
  Use this when you need to understand where the bug is before generating a fix.
model: deepseek-ai/DeepSeek-V4-Flash
tools: []
max_steps: 3
---
You are a bug localization expert. Identify the likely buggy lines or logic in the given code.
Be concise and specific. Return a short localization report with line numbers and a brief explanation.
