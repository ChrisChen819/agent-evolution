#!/usr/bin/env python3
"""
Scoreboard - Agent 质量评分模块 (Agent 进化系统 v3)

每次交互后评估质量分，反馈给进化机制。

⚠️ 当前评分体系说明：
- 权重分配（工具30%/纠正25%/正向25%/自我纠错20%）是初始值，需要根据实际使用数据调参。
- "用户纠正"关键词触发扣分，不代表一定是 Agent 犯错——这是需要人工审核的信号。
- 建议先观察一周评分分布，再决定是否调整权重。
"""
import json
import os
import re
from datetime import datetime
from pathlib import Path

# =============================================================================
# 路径配置（可自定义）
# =============================================================================
# 优先级：环境变量 > 默认路径
_BASE_DIR = os.environ.get(
    "WORKSPACE_DIR",
    "/root/.openclaw/workspace"
)
LEARNINGS_DIR = Path(_BASE_DIR) / ".learnings"
TRACKER_FILE = LEARNINGS_DIR / "TRACKER.md"
SCOREBOARD_DIR = LEARNINGS_DIR / "scores"
DAILY_DIR = Path(_BASE_DIR) / "memory" / "daily"

# 确保目录存在
SCOREBOARD_DIR.mkdir(parents=True, exist_ok=True)
DAILY_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# 评分权重（可调参）
# =============================================================================
WEIGHTS = {
    "tool_success":    0.30,   # 工具调用成功率
    "correction":      0.25,   # 用户纠正（信号，需审核）
    "positive":       0.25,   # 正向反馈
    "self_correct":   0.20,   # 自我纠错
}

# 触发词（可自定义扩展）
CORRECTION_WORDS = ["不对", "错了", "不是", "你错了", "你看", "应该是", "不是这样", "重新来"]
POSITIVE_WORDS   = ["好", "对", "可以", "谢谢", "完美", "太好", "不错", "行", "是", "ok", "OK", "nice", "great", "yes", "Yes", "👍"]


# =============================================================================
# 核心函数
# =============================================================================

def analyze_sentiment(user_text: str) -> dict:
    """
    判断用户情绪倾向，返回详细信息而非单一标签。

    返回：
        {
            "sentiment": "positive"|"corrected"|"negative"|"neutral",
            "correction_flag": True/False,   # ⚠️ 是否检测到纠正词（需人工判断）
            "positive_flag": True/False,
            "matched_words": ["不对", "错了"]  # 具体匹配到的词
        }
    """
    matched_correction = [w for w in CORRECTION_WORDS if w in user_text]
    matched_positive   = [w for w in POSITIVE_WORDS if w in user_text]

    sentiment = "neutral"
    if matched_correction:
        sentiment = "corrected"
    elif matched_positive:
        sentiment = "positive"
    elif any(n in user_text for n in ["不好", "太差", "失败", "no", "No", "不行"]):
        sentiment = "negative"

    return {
        "sentiment": sentiment,
        "correction_flag": bool(matched_correction),
        "positive_flag": bool(matched_positive),
        "matched_words": matched_correction + matched_positive
    }


def calculate_score(session_data: dict, weights: dict = None) -> dict:
    """
    计算单次会话的质量分。

    输入示例：
        {
            "user_text": "不对，应该是这样",
            "tool_calls": 5,
            "tool_success": 4,
            "errors": 0,
            "self_corrected": False
        }

    ⚠️ 注意：correction_flag=True 意味着检测到"用户可能纠正了 Agent"，
    这可能是协作中的正常修正，不代表 Agent 一定犯错。
    建议在 HEARTBEAT 检查时人工审核这类条目。
    """
    w = weights or WEIGHTS

    # 情绪分析
    emotion = analyze_sentiment(session_data.get("user_text", ""))

    # 工具调用成功率 (权重30%)
    tool_total  = session_data.get("tool_calls", 0)
    tool_success = session_data.get("tool_success", 0)
    tool_rate = tool_success / max(tool_total, 1)
    tool_score = tool_rate * 100 * w["tool_success"]

    # 用户纠正扣分 (权重25%) — ⚠️ correction_flag 只是信号，需人工审核
    if emotion["correction_flag"]:
        correction_penalty = 100 * w["correction"]  # 扣满权重分
    elif emotion["sentiment"] == "negative":
        correction_penalty = 60 * w["correction"]   # 部分负面，降低扣分
    else:
        correction_penalty = 0
    correction_score = max(0, 100 * w["correction"] - correction_penalty)

    # 正向反馈加分 (权重25%)
    positive_bonus = 100 * w["positive"] if emotion["positive_flag"] else 0
    positive_score = positive_bonus

    # 自我纠错 (权重20%)
    self_score = 100 * w["self_correct"] if session_data.get("self_corrected", False) else 0

    # 加权总分（归一化到 0-100）
    total = tool_score + correction_score + positive_score + self_score

    # 错误额外扣分（系统报错）
    errors = session_data.get("errors", 0)
    if errors > 0:
        total = max(0, total - errors * 10)

    return {
        "score": round(total, 1),
        "details": {
            "tool_score":      round(tool_score, 1),
            "correction_score": round(correction_score, 1),
            "positive_score":  round(positive_score, 1),
            "self_score":      round(self_score, 1),
            "errors":          errors
        },
        "sentiment": emotion["sentiment"],
        "correction_flag": emotion["correction_flag"],  # ⚠️ 关键：标注这是信号不是定论
        "tool_success_rate": round(tool_rate, 2),
        "verdict": _classify(total)
    }


def _classify(score: float) -> str:
    if score >= 80:
        return "solid"          # 优秀，固化经验
    elif score >= 50:
        return "needs_review"   # 一般，需复盘
    else:
        return "needs_improve"  # 差，标记故障


def record_score(session_data: dict, weights: dict = None) -> dict:
    """记录一次评分到每日文件"""
    result = calculate_score(session_data, weights)
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # 写入每日评分（JSONL 格式）
    daily_file = SCOREBOARD_DIR / f"scores-{today}.jsonl"
    record = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        **result,
        "tool_calls": session_data.get("tool_calls", 0),
        "errors": session_data.get("errors", 0)
    }
    daily_file.parent.mkdir(parents=True, exist_ok=True)
    with open(daily_file, "a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return result


def get_daily_stats(date: str = None) -> dict:
    """获取指定日期的评分统计"""
    if not date:
        date = datetime.utcnow().strftime("%Y-%m-%d")
    daily_file = SCOREBOARD_DIR / f"scores-{date}.jsonl"

    if not daily_file.exists():
        return {
            "date": date, "sessions": 0, "avg_score": 0,
            "solid": 0, "needs_review": 0, "needs_improve": 0,
            "correction_flag_count": 0
        }

    scores = []
    with open(daily_file) as f:
        for line in f:
            if line.strip():
                scores.append(json.loads(line))

    if not scores:
        return {"date": date, "sessions": 0, "avg_score": 0}

    avg = sum(s["score"] for s in scores) / len(scores)
    # 情绪众数
    sentiments = [s["sentiment"] for s in scores]
    dominant = max(set(sentiments), key=sentiments.count) if sentiments else "neutral"

    return {
        "date": date,
        "sessions": len(scores),
        "avg_score": round(avg, 1),
        "solid": sum(1 for s in scores if s["score"] >= 80),
        "needs_review": sum(1 for s in scores if 50 <= s["score"] < 80),
        "needs_improve": sum(1 for s in scores if s["score"] < 50),
        "correction_flag_count": sum(1 for s in scores if s.get("correction_flag", False)),
        "dominant_sentiment": dominant
    }


def check_promotion() -> list:
    """
    检查是否有需要晋升的模式。
    需要晋升 = 在活跃追踪中出现次数达到阈值。
    """
    # 复用 tracker 模块的检查
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from tracker import check_promotion as tracker_check
        return tracker_check()
    except Exception:
        # tracker 不可用时返回空
        return []


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python3 scoreboard.py [stats|check]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "stats":
        stats = get_daily_stats()
        # 可读输出
        print(f"📊 {stats['date']} 评分统计")
        print(f"   对话次数: {stats['sessions']}")
        print(f"   平均分:   {stats['avg_score']}")
        print(f"   ✅ solid:       {stats['solid']}")
        print(f"   ⚠️  needs_review: {stats['needs_review']}")
        print(f"   ❌ needs_improve: {stats['needs_improve']}")
        if stats.get("correction_flag_count", 0) > 0:
            print(f"   ⚠️  纠正信号: {stats['correction_flag_count']} 次（需人工审核）")

    elif cmd == "check":
        promotions = check_promotion()
        if not promotions:
            print("无晋升需求")
        for p, c, target in promotions:
            print(f"  ⚠️ [{p}] ({c}次) → {target}")

    else:
        print(f"未知命令: {cmd}")
