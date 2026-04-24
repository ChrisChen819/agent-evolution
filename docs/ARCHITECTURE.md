# Agent Evolution System — 架构设计详解

## 系统架构总览

```
用户交互
    ↓
┌─────────────────────────────────────┐
│          OpenClaw Agent              │
│  ┌───────────────────────────────┐  │
│  │      质量评分层 (Scoreboard)   │  │
│  │   每次交互后自动计算质量分       │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │      错误闭环层 (Tracker)     │  │
│  │   识别重复模式 → 触发晋升     │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │      触发层 (Heartbeat)      │  │
│  │   心跳检查 / 周检 / 即时纠正   │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
    ↓              ↓              ↓
┌─────────┐  ┌─────────┐  ┌─────────┐
│ MemOS   │  │ Score-  │  │ Learn-  │
│ 语义记忆 │  │ board   │  │ ings/   │
│          │  │ .jsonl  │  │ ERRORS  │
│ Qwen3   │  │         │  │ .md     │
│ Embed   │  └─────────┘  └─────────┘
└─────────┘
```

## 组件职责

### Scoreboard（质量评分模块）

**文件**：`src/scoreboard.py`

**职责**：每次交互结束后计算质量分，记录到每日文件。

**输出**：`memory/daily/scores-YYYY-MM-DD.jsonl`

```
{"timestamp": "2026-04-24 14:30 UTC", "score": 85.0, "sentiment": "positive", ...}
{"timestamp": "2026-04-24 15:00 UTC", "score": 30.0, "sentiment": "corrected", ...}
```

### Tracker（频繁模式追踪）

**文件**：`src/tracker.py`

**职责**：追踪重复出现的错误/行为模式，触发晋升。

**晋升规则**：
- 3次 → 写入 `LEARNINGS.md`
- 5次 → 晋升到 `AGENTS.md` / `TOOLS.md`
- 10次 → 自动创建独立 Skill

### Heartbeat（心跳巡检）

**触发源**：`HEARTBEAT.md`（由 OpenClaw 心跳任务驱动）

**职责**：
1. 扫描 error queue / action queue
2. 检查 scoreboard 统计
3. 运行晋升检查
4. 评估是否需要周检

### MemOS（长期语义记忆）

**职责**：提供向量化的语义记忆检索。

**接入方式**：
- embedding：Qwen/Qwen3-Embedding-8B（SiliconFlow）
- summarizer：GLM-4（智谱）
- 存储：本地 SQLite

**与进化模块的关系**：
- MemOS 负责"记住"
- Scoreboard/Tracker 负责"评估"和"晋升"
- 两者共同构成完整的长期学习闭环

## 数据流

```
用户消息
    ↓
Agent 处理
    ↓
┌──────────────────────────────────────┐
│ 1. 质量评分（Scoreboard）             │
│    写入 memory/daily/scores-*.jsonl  │
└──────────────────────────────────────┘
    ↓
┌──────────────────────────────────────┐
│ 2. 心跳巡检（定期）                   │
│    读取评分 → 识别异常模式           │
└──────────────────────────────────────┘
    ↓
┌──────────────────────────────────────┐
│ 3. 晋升检查（Tracker）               │
│    模式计数+1 → 判断晋升阈值         │
└──────────────────────────────────────┘
    ↓
┌──────────────────────────────────────┐
│ 4. 经验沉淀（MemOS + 文件系统）       │
│    固化到 MEMORY.md / AGENTS.md     │
└──────────────────────────────────────┘
```

## 文件结构

```
workspace/
├── skills/
│   └── emotion-analyzer/
│       └── src/
│           ├── scoreboard.py      # 质量评分
│           └── emotion_analyzer.py # 情绪分析
├── .learnings/
│   ├── TRACKER.md               # 频繁模式追踪表
│   ├── ERRORS.md                # 错误记录
│   ├── LEARNINGS.md             # 经验沉淀
│   ├── PROMOTIONS.md            # 晋升日志
│   └── experiences/             # 单条经验
├── memory/
│   ├── daily/
│   │   └── scores-*.jsonl      # 每日评分日志
│   └── MEMORY.md                # 长期记忆
└── HEARTBEAT.md                 # 心跳检查清单
```

## 与 OpenClaw 的集成

| OpenClaw 组件 | 集成方式 |
|--------------|---------|
| **Skill System** | `emotion-analyzer` skill 封装评分和情绪分析 |
| **Heartbeat** | `HEARTBEAT.md` 定义检查清单，OpenClaw cron 驱动 |
| **Memory System** | `memory_search` / `memory_timeline` API |
| **Agent Config** | `fallbacks` 字段支持模型切换 |
