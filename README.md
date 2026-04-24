# Agent Evolution System v3

> 让 AI Agent 从"工具"进化为"可自我成长的资产"——基于福格行为模型（B=MAP）的自主进化框架
>
> Turn your AI Agent from a static tool into a self-improving asset — powered by BJ Fogg's Behavior Model (B=MAP)

> ⚠️ **Scoring Notice**: This system flags messages containing "不对"/"错了" as potential corrections and applies penalty scores. For collaborative agents, run on a test account for one week before production use.
> ⚠️ **评分说明**：本系统对包含"不对""错了"等词的回复触发扣分信号。协作型 Agent 建议先用测试账号观察一周再投入生产。

[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## Table of Contents / 目录

- [Overview / 项目简介](#overview--项目简介)
- [Quick Start / 快速开始](#quick-start--快速开始)
- [Core: B=MAP Framework / 核心：B=MAP 框架](#core-bmap-framework--核心-bmap-框架)
- [Project Structure / 项目结构](#project-structure--项目结构)
- [Quality Scoring / 质量评分系统](#quality-scoring--质量评分系统)
- [Promotion Rules / 经验晋升规则](#promotion-rules--经验晋升规则)
- [Documentation / 文档](#documentation--文档)
- [Testing / 测试](#testing--测试)
- [License / 许可](#license--许可)

---

## Overview / 项目简介

Agent Evolution System is a **self-improvement framework for individual AI Agents**, built on BJ Fogg's Behavior Model (B=MAP).

The core problem it solves: **AI Agents repeat the same mistakes without learning from them.**

No GPU, no model retraining required. Through **quality scoring, error tracking, and experience promotion**, it enables continuous agent growth.

本项目是一个**面向单个 AI Agent 的自我进化框架**，核心理念来自 BJ Fogg 的福格行为模型（B=MAP）。

解决的核心问题：**AI Agent 重复犯同样的错误，缺乏从错误中学习的机制。**

不依赖 GPU、不需要模型重训练，通过**质量评分、错误闭环、经验晋升**三步循环让 Agent 持续进化。

---

## Quick Start / 快速开始

### Prerequisites / 前置要求

| Dependency / 依赖 | Version / 版本 | Notes / 说明 |
|-----------------|--------------|------------|
| **OpenClaw** | v2026.3+ | Agent framework (required) / Agent 框架核心（必须） |
| **Python** | 3.10+ | Runs scoring scripts / 评分脚本运行依赖 |
| **MemOS** | Latest | Semantic memory (optional) / 语义记忆（可选） |

### Supported Providers / 支持的模型提供商

| Provider / 提供商 | API Type | Recommended Model | Sign Up / 申请 |
|------------------|---------|-------------------|--------------|
| MiniMax | Anthropic Messages | MiniMax-M2.7 | api.minimax.io |
| 智谱 GLM | OpenAI Completions | GLM-5.1 / GLM-4.7 | bigmodel.cn |
| DeepSeek | OpenAI Completions | deepseek-v4-flash | platform.deepseek.com |
| OpenRouter | OpenAI Completions | Gemini series | openrouter.ai |

### One-Line Install / 一键安装

```bash
git clone https://github.com/YOUR_USERNAME/agent-evolution.git
cd agent-evolution
chmod +x scripts/setup.sh
./scripts/setup.sh
```

The install script will: / 安装脚本会：
1. Detect if OpenClaw workspace exists / 检测 workspace 是否存在
2. Copy evolution modules (skip if exists) / 复制进化模块（已存在则跳过）
3. Append supplement content to existing files (never overwrite) / 追加补充内容到现有文件（永不覆盖）
4. Check MemOS status / 检测 MemOS 状态

### Target Audience / 目标用户

**Users who have already installed OpenClaw.** This project does NOT overwrite any existing configuration. All templates are `*_SUPPLEMENT.md` format — append-only, never overwriting your existing files.

**已安装 OpenClaw 的用户。** 本项目不覆盖任何现有配置，仅向你的 workspace 添加进化能力。所有模板为 `*_SUPPLEMENT.md` 格式，是追加内容，不覆盖已有文件。

---

## Core: B=MAP Framework / 核心：B=MAP 框架

### B = Behavior（目标行为）

Desired agent behaviors we want to evolve: / 我们希望 Agent 进化的目标行为：
- Fewer repeated errors / 更少的重复错误
- More accurate tool calls / 更准确的工具调用
- Proactive problem discovery / 更主动的问题发现

### M = Motivation（驱动力）

The agent's evolution drive comes from feedback signals: / Agent 的进化动力来自**反馈信号**：

| Signal / 信号 | Type / 类型 | Implementation / 实现 |
|-------------|------------|---------------------|
| **Negative Feedback** | 用户纠正"不对"/"错了" | Record to ERRORS.md / 记录到 ERRORS.md |
| **Positive Feedback** | 用户认可"很好"/"谢谢" | Solidify to MEMORY.md / 沉淀到 MEMORY.md |
| **Periodic Review** | 系统性能力诊断 | Heartbeat + weekly check / 心跳 + 周检 |

> **Key insight**: Error feedback is more valuable than correct execution. / **关键洞察**：错误的反馈比正确的执行更有价值。

### A = Ability（能力建设）

Lowering the barrier to "doing things right": / 降低"正确做事"的门槛：

- **Skill封装**：High-frequency tasks are reusable, 10× faster than writing from scratch / 高频任务可复用，调用比手写快 10 倍
- **Fallback模型**：Automatic model switch on failure / 主模型故障时自动切换
- **持久化记忆**：MemOS + MEMORY.md + 每日笔记，跨会话不丢失

### P = Prompt（触发机制）

Triggering the right evolution behavior at the right moment: / 在对的时机触发正确的进化行为：

| Trigger / 触发 | Frequency / 频率 | Action / 做什么 |
|--------------|----------------|---------------|
| Heartbeat check / 心跳检查 | Every 4-6 hours / 每 4-6 小时 | Scan error/action queue / 扫描错误/行动队列 |
| Weekly deep review / 每周能力深检 | Sunday UTC 20:00 | System performance diagnosis / 系统性能诊断 |
| User correction / 用户纠正 | Real-time / 实时 | Record error immediately / 错误即时记录 |

---

## Project Structure / 项目结构

```
agent-evolution/
├── README.md              # This file / 本文件（中英双语）
├── LICENSE               # MIT License
├── .gitignore            # Excludes *.json, .env, memory/, etc. / 排除 *.json、.env、memory/ 等
├── scripts/
│   └── setup.sh          # Interactive install (4 steps, non-blocking) / 交互式安装（4步，不阻塞）
├── configs/
│   └── .env.example      # API Keys template (fill in yourself) / API Keys 模板（自行填写）
├── src/
│   ├── scoreboard.py     # Quality scoring module / 质量评分模块
│   ├── tracker.py        # Frequent pattern tracking + promotion engine / 频繁模式追踪 + 晋升引擎
│   └── emotion_analyzer.py # Emotion analysis engine / 情绪分析引擎
├── templates/
│   ├── SOUL_SUPPLEMENT.md       # Append to existing SOUL.md / 追加到现有 SOUL.md
│   ├── HEARTBEAT_SUPPLEMENT.md # Append to existing HEARTBEAT.md / 追加到现有 HEARTBEAT.md
│   └── AGENTS_SUPPLEMENT.md    # Append to existing AGENTS.md / 追加到现有 AGENTS.md
└── docs/
    ├── DEPLOY.md         # Detailed deployment guide (516 lines) / 详细部署文档
    ├── ARCHITECTURE.md   # Architecture design / 架构设计详解
    └── API.md            # API reference / 各模块 API 参考
```

---

## Quality Scoring / 质量评分系统

After each interaction, scores are calculated automatically: / 每次交互后自动计算质量分：

| Dimension / 维度 | Weight / 权重 | Description / 说明 |
|----------------|-------------|-------------------|
| Tool call success / 工具调用成功率 | 30% | Successful calls / total calls / 成功调用数/总数 |
| User correction / 用户纠正 | 25% | Signal only — requires human review / 信号，需人工审核 |
| Positive feedback / 正向反馈 | 25% | "好"/"谢谢"/"nice" etc. / |
| Self-correction / 自我纠错 | 20% | Whether agent self-corrected before being told / 是否主动发现并纠正 |

**Score grades / 分数分级**：/ 分级：
- **≥80 / solid**：Excellent — solidify to long-term memory / 优秀，固化经验
- **50-79 / needs_review**：Average — trigger analysis / 一般，复盘
- **<50 / needs_improve**：Poor — mark failure pattern / 差，标记故障

⚠️ `correction_flag` is a **signal, not a verdict**. It indicates the user said something that might be a correction, but requires human review — it does NOT automatically mean the agent was wrong.

⚠️ `correction_flag` 是**信号不是定论**。它表示用户说了可能是纠正的话，但需要人工审核，不代表 Agent 一定犯错。

---

## Promotion Rules / 经验晋升规则

| Repetitions / 重复次数 | Action / 处理方式 |
|----------------------|----------------|
| **3 times / 次** | Write to `LEARNINGS.md` / 写入 LEARNINGS.md |
| **5 times / 次** | Promote to `AGENTS.md` / `TOOLS.md` / 晋升到 AGENTS.md / TOOLS.md |
| **10 times / 次** | Auto-create independent Skill / 自动创建独立 Skill |

---

## Documentation / 文档

| File / 文件 | Lines / 行数 | Content / 内容 |
|-----------|------------|---------------|
| [DEPLOY.md](docs/DEPLOY.md) | 516 | Full deployment guide / 完整部署指南 |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | 140 | Component diagram + data flow / 组件图 + 数据流 |
| [API.md](docs/API.md) | 160 | Function signatures + usage examples / 函数签名 + 使用示例 |

---

## Testing / 测试

```bash
# Run quality scoring test / 运行评分测试
python3 src/scoreboard.py stats

# Run promotion check / 运行晋升检查
python3 src/scoreboard.py check

# Run tracker / 运行追踪器
python3 src/tracker.py stats
python3 src/tracker.py check

# Health check / 健康检查
bash scripts/setup.sh --check
```

---

## License / 许可

MIT License — see [LICENSE](LICENSE)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software.

本项目采用 MIT 许可证 — 详见 [LICENSE](LICENSE)
