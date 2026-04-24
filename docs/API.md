# Agent Evolution System — API 参考

## scoreboard.py

质量评分模块，提供会话级别的质量评估。

### 函数

#### `calculate_score(session_data: dict) -> dict`

计算单次会话的质量分。

**参数**：
```python
session_data = {
    "user_text": "不对，应该是这样",   # 用户原始文本
    "tool_calls": 5,                   # 工具调用总次数
    "tool_success": 4,                # 工具调用成功次数
    "errors": 1,                       # 本轮错误次数
    "self_corrected": False            # 是否自我纠错
}
```

**返回**：
```python
{
    "score": 80.0,                    # 总分
    "details": {
        "tool_score": 24.0,           # 工具得分 (30%权重)
        "correction_score": 0,         # 纠正得分 (25%权重)
        "positive_score": 25.0,       # 正向得分 (25%权重)
        "self_score": 20.0            # 自我纠错得分 (20%权重)
    },
    "sentiment": "corrected",         # 情绪: positive/neutral/corrected/negative
    "tool_success_rate": 0.8,         # 工具成功率
    "verdict": "needs_improve"        # solid / needs_review / needs_improve
}
```

#### `record_score(session_data: dict) -> dict`

记录一次评分到每日文件，同时返回评分结果。

#### `get_daily_stats(date: str = None) -> dict`

获取指定日期的评分统计。

**返回**：
```python
{
    "date": "2026-04-24",
    "sessions": 3,
    "avg_score": 63.3,
    "solid": 2,
    "needs_review": 0,
    "needs_improve": 1,
    "sentiment": "positive"
}
```

#### `check_promotion() -> list`

检查是否有模式需要晋升。

**返回**：
```python
[
    ("tool_call_schema_rejected", 3, "LEARNINGS"),  # (模式名, 次数, 晋升目标)
    ("duplicate_response", 5, "TOOLS/AGENTS")
]
```

---

## tracker.py

频繁模式追踪模块。

### 函数

#### `bump_pattern(pattern: str) -> int`

将指定模式的出现次数 +1，返回更新后的次数。

```python
bump_pattern("tool_call_schema_rejected")
# → 4  （返回更新后的次数）
```

**晋升触发**：
- 达到 3次 → 追加到 `LEARNINGS.md`
- 达到 5次 → 晋升到 `AGENTS.md` / `TOOLS.md`
- 达到 10次 → 自动创建 Skill

#### `_init_tracker()`

初始化追踪文件 `TRACKER.md`（若不存在）。

---

## emotion_analyzer.py

情绪分析引擎，提供细粒度的用户情绪识别。

### 函数

#### `analyze_emotions(text: str) -> dict`

分析文本中的情绪。

```python
result = analyze_emotions("太棒了！这正是我想要的")
# → {
#     "primary": "成就感",
#     "intensity": 3,
#     "tags": ["success", "completion"]
#   }
```

### 支持的情绪类型

| 情绪 | 强度 | 触发词示例 |
|------|------|---------|
| 成就感 | 3 | 太棒了、完美、正是我要的 |
| 挫败感 | 3 | 不对、错了、不好 |
| 困惑 | 2 | 不确定、不太懂、怎么办 |
| 温暖 | 3 | 谢谢、感谢、爱了 |
| 好奇 | 2 | 为什么、怎么做到的 |
| 平静 | 1 | 可以、还行、ok |

---

## 命令行使用

```bash
# 查看当日评分统计
python3 src/scoreboard.py stats

# 检查晋升需求
python3 src/scoreboard.py check

# 分析情绪
python3 src/emotion_analyzer.py "太棒了"

# 更新模式计数
python3 src/tracker.py "tool_call_schema_rejected"
```

---

## 数据存储路径

| 数据类型 | 路径 |
|---------|------|
| 每日评分 | `memory/daily/scores-YYYY-MM-DD.jsonl` |
| 错误记录 | `.learnings/ERRORS.md` |
| 经验沉淀 | `.learnings/LEARNINGS.md` |
| 模式追踪 | `.learnings/TRACKER.md` |
| 晋升日志 | `.learnings/PROMOTIONS.md` |
| 长期记忆 | `MEMORY.md` |
