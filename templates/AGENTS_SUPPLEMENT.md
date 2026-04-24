# AGENTS.md 补充内容

> ⚠️ **这是补充内容，不是完整文件。**
> 已安装 OpenClaw 的用户请将以下章节**追加到**你现有的 `AGENTS.md` 中对应位置，不要直接覆盖。

---

## 添加以下章节到你的 AGENTS.md

### 1. 进化相关文件（添加）

在"Memory"或"文件结构"章节添加：

```markdown
### 进化相关文件

| 文件 | 作用 |
|------|------|
| `.learnings/ERRORS.md` | 每次错误记录 |
| `.learnings/LEARNINGS.md` | 经验沉淀索引 |
| `.learnings/TRACKER.md` | 频繁模式追踪 |
| `.learnings/experiences/` | 单条经验存储 |
| `memory/daily/scores-*.jsonl` | 每日质量评分日志 |
| `skills/emotion-analyzer/src/scoreboard.py` | 评分系统 |
```

### 2. Skill 安装规范（添加）

在"Tools"或"Safety"章节后添加：

```markdown
### 第三方 Skill 安全审核

安装前必须检查：
1. 搜索安全评价/风险报告
2. 检查源码（网络请求、数据发送）
3. 确认无后门再安装

安装命令：`openclaw skill install <skill-id>`
```

### 3. 自我纠错机制（添加）

```markdown
### 元错误识别

发现以下情况时立即主动汇报：
- 混淆了两个不同实例/会话的消息
- 误判用户意图
- 执行了用户未明确授权的操作
- 重复执行同一任务

汇报格式：
> ⚠️ 元错误自检：
> 我犯了一个错误：[描述]
> 原因：[为什么会错]
> 修正：[我已经做了什么]
```
