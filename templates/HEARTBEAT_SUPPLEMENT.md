# HEARTBEAT.md 补充内容

> ⚠️ **这是补充内容，不是完整文件。**
> 已安装 OpenClaw 的用户请将以下内容**追加到**你现有的 `HEARTBEAT.md` 中对应位置，不要直接覆盖。

---

## 添加以下检查项到你的心跳清单

找到 HEARTBEAT.md 中的"检查清单"章节，在现有检查项末尾添加：

### 进化系统检查（每次心跳）

```markdown
- [ ] **错误队列检查**：读取 `/tmp/.error-queue`，如有条目立即处理
- [ ] **行动队列检查**：读取 `/tmp/.action-queue`，按优先级执行
- [ ] **质量评分统计**：运行 `python3 skills/emotion-analyzer/src/scoreboard.py stats`
- [ ] **晋升检查**：运行 `python3 skills/emotion-analyzer/src/scoreboard.py check`
  - 3次 → 追加到 `.learnings/LEARNINGS.md`
  - 5次 → 晋升到 `AGENTS.md` / `TOOLS.md`
  - 10次 → 创建新 Skill
```

### 每日快照（心跳时静默执行，不发报告）

```markdown
- [ ] 扫描当日新增 ERROR 条目
- [ ] 判断是否有实质性新内容：
  - 有（>0条）→ 更新 `memory/daily/YYYY-MM-DD.md`，不发报告
  - 无 → 完全静默，回复 HEARTBEAT_OK
```

---

## 快速检查清单

在你的 HEARTBEAT.md 中搜索：

| 检查项 | 如无则添加 |
|--------|---------|
| `error-queue` | → 添加"错误队列检查" |
| `scoreboard` | → 添加"质量评分统计" |
| `check_promotion` | → 添加"晋升检查" |
| 每日快照 | → 添加上方"每日快照"章节 |
