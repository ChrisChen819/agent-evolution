#!/usr/bin/env python3
"""
Frequent Pattern Tracker — 频繁模式追踪 + 晋升引擎
Agent 进化系统 v3 核心组件

使用方法:
  python3 tracker.py bump <pattern>   # 模式出现次数 +1，返回更新后的计数
  python3 tracker.py stats            # 查看当前追踪状态
  python3 tracker.py check            # 检查需要晋升的条目
"""
import os
import re
import json
from pathlib import Path
from datetime import datetime

# =============================================================================
# 路径配置（可自定义，通过环境变量覆盖）
# =============================================================================
_WORKSPACE = os.environ.get(
    "WORKSPACE_DIR",
    os.environ.get("AGENT_EVOLUTION_LEARNS", "/root/.openclaw/workspace")
).replace("/.learnings", "")  # 兼容 AGENT_EVOLUTION_LEARNS 传完整路径

_LEARNS_DIR = Path(_WORKSPACE) / ".learnings"
TRACKER_FILE = _LEARNS_DIR / "TRACKER.md"
PROMOTIONS_FILE = _LEARNS_DIR / "PROMOTIONS.md"
BACKUP_FILE = _LEARNS_DIR / "tracker_backup.jsonl"

# =============================================================================
# 晋升规则（阈值可调）
# =============================================================================
PROMOTION_RULES = [
    {"threshold": 3,  "target": "LEARNINGS", "action": "写入经验库"},
    {"threshold": 5,  "target": "AGENTS",     "action": "晋升核心规则"},
    {"threshold": 10, "target": "SKILL",      "action": "自动创建 Skill"},
]

# =============================================================================
# 核心函数
# =============================================================================

def bump_pattern(pattern: str) -> int:
    """
    将一个模式的出现次数 +1，返回更新后的真实计数（≥1）。
    首次出现计为 1，重复出现依次递增。
    达到晋升阈值时自动触发晋升动作。
    """
    _LEARNS_DIR.mkdir(parents=True, exist_ok=True)

    if not TRACKER_FILE.exists():
        _init_tracker()

    content = TRACKER_FILE.read_text()
    lines = content.split('\n')

    updated_count = None  # 成功更新时的计数

    for i, line in enumerate(lines):
        if not _is_data_row(line):
            continue
        if pattern not in line:
            continue

        # 在活跃追踪区域内才处理
        section = _get_section(lines, i)
        if section != "active":
            continue

        parts = [p.strip() for p in line.split('|') if p.strip()]
        if len(parts) < 2:
            continue
        try:
            count_col = _find_count_column(parts, lines, i)
            if count_col < 0:
                continue

            new_count = int(parts[count_col]) + 1
            parts[count_col] = str(new_count)

            # 更新时间列（最近）
            date_col = _find_date_column(parts, lines, i)
            if date_col >= 0:
                parts[date_col] = _stamp()

            # 状态列
            status_col = _find_status_column(parts, lines, i)
            if status_col >= 0:
                promoted = _check_and_promote(pattern, new_count)
                if promoted:
                    parts[status_col] = f"⚠️ → {promoted}"
                elif parts[status_col].startswith("⚠️"):
                    parts[status_col] = "🆕 活跃"

            # 重建行
            lines[i] = _build_row(parts, lines, i)
            updated_count = new_count
            break

        except (ValueError, IndexError):
            pass

    if updated_count is None:
        # 未找到匹配 → 新增一行到活跃追踪表格
        new_row = [pattern, "1", _stamp(), _stamp(), "🆕 新增"]
        lines = _inject_active_row(lines, new_row)
        updated_count = 1

    TRACKER_FILE.write_text('\n'.join(lines))
    _backup({"op": "bump", "pattern": pattern, "count": updated_count})
    return updated_count


def get_count(pattern: str) -> int:
    """查询某模式当前出现次数，不修改任何内容"""
    if not TRACKER_FILE.exists():
        return 0
    lines = TRACKER_FILE.read_text().split('\n')
    for i, line in enumerate(lines):
        if not _is_data_row(line):
            continue
        if pattern not in line:
            continue
        if _get_section(lines, i) != "active":
            continue
        parts = [p.strip() for p in line.split('|') if p.strip()]
        try:
            col = _find_count_column(parts, lines, i)
            return int(parts[col]) if col >= 0 else 0
        except (ValueError, IndexError):
            return 0
    return 0


def stats() -> dict:
    """返回当前活跃追踪状态"""
    if not TRACKER_FILE.exists():
        return {"active": []}

    lines = TRACKER_FILE.read_text().split('\n')
    active = []

    for i, line in enumerate(lines):
        if not _is_data_row(line):
            continue
        if _get_section(lines, i) != "active":
            continue
        parts = [p.strip() for p in line.split('|') if p.strip()]
        if len(parts) < 4:
            continue
        try:
            count_col = _find_count_column(parts, lines, i)
            if count_col < 0:
                continue
            count = int(parts[count_col])
            next_t = next((r["threshold"] for r in PROMOTION_RULES
                           if r["threshold"] > count), None)
            active.append({
                "pattern":   parts[_find_name_column(parts, lines, i)],
                "count":     count,
                "first":     parts[_find_first_column(parts, lines, i)],
                "last":      parts[_find_date_column(parts, lines, i)],
                "status":    parts[_find_status_column(parts, lines, i)],
                "remaining": (next_t - count) if next_t else None
            })
        except (ValueError, IndexError):
            pass

    return {"active": active}


def check_promotion() -> list:
    """检查达到晋升阈值的条目，每个模式只返回最高满足阈值"""
    st = stats()
    result = []
    seen = set()
    for item in st["active"]:
        count = item["count"]
        highest = None
        for rule in PROMOTION_RULES:
            if count >= rule["threshold"]:
                highest = rule
        if highest and item["pattern"] not in seen:
            result.append({
                "pattern":   item["pattern"],
                "count":     count,
                "threshold": highest["threshold"],
                "target":    highest["target"],
                "action":    highest["action"]
            })
            seen.add(item["pattern"])
    return result


# =============================================================================
# 私有函数
# =============================================================================

def _check_and_promote(pattern: str, count: int) -> str | None:
    """达到晋升阈值则执行晋升，返回晋升目标；否则 None"""
    for rule in PROMOTION_RULES:
        if count == rule["threshold"]:
            _do_promote(pattern, rule)
            return rule["target"]
    return None


def _do_promote(pattern: str, rule: dict):
    """写入晋升日志"""
    entry = (
        f"- {_stamp()} | [{pattern}] 达到 {rule['threshold']}次 "
        f"→ {rule['action']}（{rule['target']}）"
    )
    PROMOTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing = PROMOTIONS_FILE.read_text() if PROMOTIONS_FILE.exists() else ""
    PROMOTIONS_FILE.write_text(entry + "\n" + existing)


def _get_section(lines: list, line_idx: int) -> str:
    """判断给定行索引属于哪个区域。
    
    活跃追踪区域：从"## 当前活跃追踪"到"## 已处理记录"之前的区域。
    "---" 本身属于活跃区域（表格内分隔线），不触发区域切换。
    "---" 只有在紧跟"##"标题时才表示区域结束。
    """
    active_start = -1
    active_end = len(lines)
    processed_start = len(lines)

    for i, line in enumerate(lines):
        stripped = line.strip()
        if "## 当前活跃追踪" in stripped:
            active_start = i
        elif "## 已处理记录" in stripped:
            active_end = i
            processed_start = i
            break

    return "active" if active_start <= line_idx < processed_start else "processed"


def _is_data_row(line: str) -> bool:
    """判断是否是需要处理的数据行"""
    stripped = line.strip()
    if not stripped or stripped.startswith('#') or stripped.startswith('>'):
        return False
    if all(c in '-|: ' for c in stripped):
        return False  # 分隔线或纯边框
    if stripped.startswith('_') or '模式' in line:
        return False  # placeholder 或表头
    return '|' in stripped


def _find_count_column(parts: list, lines: list, line_idx: int) -> int:
    """从表头行找到次数列的索引（兼容多种列名）"""
    # 向上扫描找最近的表头
    for offset in range(1, 5):
        check_idx = line_idx - offset
        if check_idx < 0:
            break
        header_line = lines[check_idx].strip()
        if '|' not in header_line:
            continue
        if all(c in '-|: ' for c in header_line):
            continue  # 跳过边框
        if '模式' not in header_line and '次数' not in header_line:
            continue

        header_parts = [p.strip() for p in header_line.split('|') if p.strip()]
        for j, hp in enumerate(header_parts):
            # 匹配各种列名
            if hp in ("次数", "出现次数", "count", "Count"):
                return j
        # 未匹配列名 → 返回默认值（跳过此行）
        return -1
    return 1  # 默认第2列（索引1）


def _find_name_column(parts: list, lines: list, line_idx: int) -> int:
    for offset in range(1, 5):
        check_idx = line_idx - offset
        if check_idx < 0:
            break
        header_line = lines[check_idx].strip()
        if '|' not in header_line:
            continue
        if all(c in '-|: ' for c in header_line):
            continue
        if '模式' not in header_line:
            continue
        header_parts = [p.strip() for p in header_line.split('|') if p.strip()]
        for j, hp in enumerate(header_parts):
            if hp in ("模式", "pattern", "Pattern"):
                return j
    return 0


def _find_first_column(parts: list, lines: list, line_idx: int) -> int:
    for offset in range(1, 5):
        check_idx = line_idx - offset
        if check_idx < 0:
            break
        header_line = lines[check_idx].strip()
        if '|' not in header_line:
            continue
        if all(c in '-|: ' for c in header_line):
            continue
        if '首次' not in header_line and 'first' not in header_line.lower():
            continue
        header_parts = [p.strip() for p in header_line.split('|') if p.strip()]
        for j, hp in enumerate(header_parts):
            if hp in ("首次", "first", "First"):
                return j
    return 2


def _find_date_column(parts: list, lines: list, line_idx: int) -> int:
    for offset in range(1, 5):
        check_idx = line_idx - offset
        if check_idx < 0:
            break
        header_line = lines[check_idx].strip()
        if '|' not in header_line:
            continue
        if all(c in '-|: ' for c in header_line):
            continue
        if '最近' not in header_line and 'last' not in header_line.lower():
            continue
        header_parts = [p.strip() for p in header_line.split('|') if p.strip()]
        for j, hp in enumerate(header_parts):
            if hp in ("最近", "last", "Last"):
                return j
    return 3


def _find_status_column(parts: list, lines: list, line_idx: int) -> int:
    for offset in range(1, 5):
        check_idx = line_idx - offset
        if check_idx < 0:
            break
        header_line = lines[check_idx].strip()
        if '|' not in header_line:
            continue
        if all(c in '-|: ' for c in header_line):
            continue
        if '状态' not in header_line and 'status' not in header_line.lower():
            continue
        header_parts = [p.strip() for p in header_line.split('|') if p.strip()]
        for j, hp in enumerate(header_parts):
            if hp in ("状态", "status", "Status"):
                return j
    return 4


def _build_row(parts: list, lines: list, line_idx: int) -> str:
    """用 parts 数组重建一行，在表头右侧添加边框"""
    count_col = _find_count_column(parts, lines, line_idx)
    name_col  = _find_name_column(parts, lines, line_idx)
    first_col = _find_first_column(parts, lines, line_idx)
    date_col  = _find_date_column(parts, lines, line_idx)
    status_col = _find_status_column(parts, lines, line_idx)

    # 确认列数正确
    cols = [name_col, count_col, first_col, date_col, status_col]
    if len(set(cols)) != len(cols):
        # 列重叠，用默认值
        name_col, count_col, first_col, date_col, status_col = 0, 1, 2, 3, 4

    return (
        f"| {parts[name_col]} | {parts[count_col]} | {parts[first_col]} | "
        f"{parts[date_col]} | {parts[status_col]} |"
    )


def _inject_active_row(lines: list, new_row: list) -> list:
    """
    将新行插入到"当前活跃追踪"表格中，替换 placeholder 行。
    """
    result = []
    replaced = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not replaced and (
            stripped.startswith('|_') or
            ('|' in line and '_' in stripped and '活跃记录' in stripped)
        ):
            # 找到 placeholder 行，用新数据行替换
            result.append(
                f"| {new_row[0]} | {new_row[1]} | {new_row[2]} | "
                f"{new_row[3]} | {new_row[4]} |"
            )
            replaced = True
        else:
            result.append(line)

    if not replaced:
        # 如果没找到 placeholder，在表格最后一行后添加
        for i in range(len(lines) - 1, -1, -1):
            stripped = lines[i].strip()
            if stripped and '|' in stripped and not all(c in '-|: ' for c in stripped):
                result.insert(i + 1,
                    f"| {new_row[0]} | {new_row[1]} | {new_row[2]} | "
                    f"{new_row[3]} | {new_row[4]} |"
                )
                replaced = True
                break
        if not replaced:
            result.append(
                f"| {new_row[0]} | {new_row[1]} | {new_row[2]} | "
                f"{new_row[3]} | {new_row[4]} |"
            )

    return result


def _stamp():
    return datetime.utcnow().strftime("%Y-%m-%d")


def _backup(data: dict):
    """写入 JSONL 备份（防 Markdown 损坏）"""
    BACKUP_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(BACKUP_FILE, "a") as f:
        f.write(json.dumps({"ts": _stamp(), **data}, ensure_ascii=False) + "\n")


def _init_tracker():
    """初始化空的追踪文件"""
    header = (
        "# 频繁模式追踪\n\n"
        "> 由 Agent 进化系统 v3 自动维护\n"
        "> 规则：3次→LEARNINGS | 5次→AGENTS | 10次→SKILL\n"
        f"> 初始化: {_stamp()}\n\n"
        "## 当前活跃追踪\n\n"
        "| 模式 | 次数 | 首次 | 最近 | 状态 |\n"
        "|------|------|------|------|------|\n"
        "_(暂无活跃记录)_ | - | - | - | - |\n\n"
        "---\n\n"
        "## 已处理记录\n\n"
        "| 模式 | 最终次数 | 处理日期 | 晋升目标 | 状态 |\n"
        "|------|---------|---------|---------|------|\n"
        "_(暂无)_ | - | - | - | - |\n"
    )
    _LEARNS_DIR.mkdir(parents=True, exist_ok=True)
    TRACKER_FILE.write_text(header)


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "bump":
        if len(sys.argv) < 3:
            print("用法: tracker.py bump <pattern>")
            sys.exit(1)
        count = bump_pattern(sys.argv[2])
        print(f"[{sys.argv[2]}] 计数更新 → {count}")

    elif cmd == "stats":
        st = stats()
        print("当前活跃模式：")
        if not st["active"]:
            print("  （无）")
        for item in st["active"]:
            rem = f"距晋升还差 {item['remaining']} 次" if item["remaining"] else "已达最高阈值"
            print(f"  [{item['pattern']}] ×{item['count']} | {rem}")

    elif cmd == "check":
        result = check_promotion()
        if not result:
            print("无晋升需求")
        for item in result:
            print(f"  ⚠️ [{item['pattern']}] {item['count']}次 → {item['target']}（{item['action']}）")

    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
