#!/usr/bin/env python3
"""
Emotion Analyzer - 情绪分析引擎
从任务执行和用户反馈中分析情绪，生成关键词
"""
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 配置
MEMORY_DIR = Path(__file__).parent.parent / "memory"
EXPERIENCES_FILE = MEMORY_DIR / "experiences.md"
FAILURES_FILE = MEMORY_DIR / "failures.md"

# 情绪矩阵
EMOTION_MATRIX = {
    # 核心情绪 (6种)
    "成就感": {
        "positive_patterns": ["太棒了", "完美", "正是我要的", "很好", "对了", "谢谢", "搞定", "完成", "解决了"],
        "intensity": 3,
        "tags": ["success", "completion"]
    },
    "挫败感": {
        "negative_patterns": ["不对", "错了", "不好", "太差", "失败", "崩溃", "错误", "气死了"],
        "intensity": 3,
        "tags": ["failure", "error"]
    },
    "好奇": {
        "curious_patterns": ["为什么", "怎么做到的", "是什么", "how", "why", "tell me more", "发现", "新"],
        "intensity": 2,
        "tags": ["learning", "inquiry"]
    },
    "温暖": {
        "warmth_patterns": ["谢谢", "感谢", "感恩", "太好了", "帮大忙", "爱了"],
        "intensity": 3,
        "tags": ["connection", "appreciation"]
    },
    "困惑": {
        "confused_patterns": ["不确定", "不太懂", "迷茫", "怎么办", "不太对", "有点问题"],
        "intensity": 2,
        "tags": ["uncertainty", "confusion"]
    },
    "平静": {
        "neutral_patterns": ["可以", "还行", "ok", "可以吧", "收到"],
        "intensity": 1,
        "tags": ["neutral"]
    },
    # 复合情绪
    "挫败+反思": {
        "patterns": ["失败", "反思", "又错了", "一直"],
        "intensity": 3,
        "tags": ["failure", "reflection"]
    },
    "成就感+谦虚": {
        "patterns": ["成功", "但要", "继续努力"],
        "intensity": 2,
        "tags": ["success", "humble"]
    },
    "好奇+警惕": {
        "patterns": ["发现", "但要", "验证", "确认"],
        "intensity": 2,
        "tags": ["learning", "caution"]
    },
}

# 场景分类
SCENES = {
    "task_execution": {
        "keywords": ["执行", "完成", "解决", "搞定", "部署", "修复"],
        "weight": 1.0
    },
    "discussion": {
        "keywords": ["讨论", "看看", "分析", "觉得", "认为", "怎么看"],
        "weight": 0.8
    },
    "feedback": {
        "keywords": ["很好", "不对", "谢谢", "为什么", "太棒了", "错了"],
        "weight": 1.0
    },
    "learning": {
        "keywords": ["学到", "发现", "新", "研究", "看看"],
        "weight": 0.9
    },
    "problem_solving": {
        "keywords": ["问题", "错误", "失败", "解决", "排查"],
        "weight": 1.0
    }
}


class EmotionAnalyzer:
    def __init__(self):
        self.results = []
    
    def analyze(self, messages: List[Dict], tasks: List[Dict]) -> Dict:
        """分析输入，生成情绪记录"""
        
        # 1. 场景分析
        scene = self.analyze_scene(messages)
        
        # 2. 反馈分析
        feedback = self.analyze_feedback(messages)
        
        # 3. 任务分析
        task_analysis = self.analyze_tasks(tasks)
        
        # 4. 综合判断情绪
        emotion = self.synthesize_emotion(feedback, task_analysis, scene)
        
        # 5. 生成关键词
        keywords = self.generate_keywords(emotion, feedback, tasks, scene)
        
        return {
            "scene": scene,
            "feedback": feedback,
            "tasks": task_analysis,
            "emotion": emotion,
            "keywords": keywords,
            "should_record": self.should_record(emotion, feedback, task_analysis)
        }
    
    def analyze_scene(self, messages: List[Dict]) -> Dict:
        """分析主要场景"""
        scene_scores = {scene: 0 for scene in SCENES}
        
        for msg in messages:
            content = msg.get("content", "")
            for scene, config in SCENES.items():
                for kw in config["keywords"]:
                    if kw in content:
                        scene_scores[scene] += config["weight"]
        
        main_scene = max(scene_scores, key=scene_scores.get)
        total = sum(scene_scores.values())
        
        return {
            "main_scene": main_scene,
            "scores": scene_scores,
            "confidence": scene_scores[main_scene] / total if total > 0 else 0
        }
    
    def analyze_feedback(self, messages: List[Dict]) -> Dict:
        """分析用户反馈"""
        feedback_items = []
        
        for msg in messages:
            content = msg.get("content", "")
            content_lower = content.lower()
            
            # 检测反馈类型 - 中文优先
            if any(p in content for p in ["太棒了", "完美", "正是我要的", "爱了"]):
                feedback_items.append({"type": "very_positive", "intensity": 5, "content": content})
            elif any(p in content for p in ["很好", "对了", "不错", "搞定", "完成", "解决了"]):
                feedback_items.append({"type": "positive", "intensity": 3, "content": content})
            elif any(p in content for p in ["不对", "错了", "不好", "太差"]):
                feedback_items.append({"type": "negative", "intensity": 3, "content": content})
            elif any(p in content for p in ["完全不对", "气死了", "崩溃", "失败"]):
                feedback_items.append({"type": "very_negative", "intensity": 5, "content": content})
            elif any(p in content for p in ["谢谢", "感谢", "感恩"]):
                feedback_items.append({"type": "gratitude", "intensity": 3, "content": content})
            # 英文
            elif any(p in content_lower for p in ["excellent", "perfect", "great"]):
                feedback_items.append({"type": "very_positive", "intensity": 5, "content": content})
            elif any(p in content_lower for p in ["good", "thanks", "well done"]):
                feedback_items.append({"type": "positive", "intensity": 3, "content": content})
            elif any(p in content_lower for p in ["wrong", "bad", "failed", "error"]):
                feedback_items.append({"type": "negative", "intensity": 3, "content": content})
        
        return {
            "items": feedback_items,
            "has_positive": any(f["intensity"] > 0 for f in feedback_items),
            "has_negative": any(f["type"] in ["negative", "very_negative"] for f in feedback_items)
        }
    
    def analyze_tasks(self, tasks: List[Dict]) -> Dict:
        """分析任务状态"""
        completed = sum(1 for t in tasks if t.get("status") == "completed")
        failed = sum(1 for t in tasks if t.get("status") == "failed")
        
        return {
            "total": len(tasks),
            "completed": completed,
            "failed": failed,
            "success_rate": completed / len(tasks) if tasks else 0
        }
    
    def synthesize_emotion(self, feedback: Dict, tasks: Dict, scene: Dict) -> Dict:
        """综合判断情绪"""
        
        # 基于反馈
        if feedback["has_positive"]:
            return {"primary": "成就感", "intensity": 3, "source": "feedback"}
        
        if feedback["has_negative"]:
            return {"primary": "挫败感", "intensity": 3, "source": "feedback"}
        
        # 基于任务
        if tasks["failed"] > 0:
            return {"primary": "挫败感", "intensity": 3, "source": "task"}
        
        if tasks["completed"] > 0:
            return {"primary": "成就感", "intensity": 2, "source": "task"}
        
        # 基于场景
        if scene["main_scene"] == "learning":
            return {"primary": "好奇", "intensity": 2, "source": "scene"}
        
        return {"primary": "平静", "intensity": 1, "source": "default"}
    
    def generate_keywords(self, emotion: Dict, feedback: Dict, tasks: Dict, scene: Dict) -> Dict:
        """生成关键词"""
        
        event = scene.get("main_scene", "unknown")
        
        lessons = {
            "成就感": "这个方法有效，以后可以继续用",
            "挫败感": "需要分析根因，避免重复",
            "好奇": "保持好奇会带来更多发现",
            "困惑": "以后要先问清楚",
            "温暖": "珍惜连接，持续用心",
            "平静": "保持专业，持续精进"
        }
        
        improvements = {
            "成就感": "保持现状，继续精进",
            "挫败感": "分析问题，改进方法",
            "好奇": "深入研究，记录发现",
            "困惑": "主动询问，明确需求",
            "温暖": "珍惜每一次连接",
            "平静": "保持稳定输出"
        }
        
        return {
            "emotion": emotion["primary"],
            "intensity": emotion["intensity"],
            "event": event,
            "lesson": lessons.get(emotion["primary"], "持续学习"),
            "improvement": improvements.get(emotion["primary"], "保持观察"),
            "tags": EMOTION_MATRIX.get(emotion["primary"], {}).get("tags", ["general"])
        }
    
    def should_record(self, emotion: Dict, feedback: Dict, tasks: Dict) -> bool:
        """判断是否需要记录"""
        
        # 有明确反馈
        if feedback["has_positive"] or feedback["has_negative"]:
            return True
        
        # 任务失败
        if tasks["failed"] > 0:
            return True
        
        # 情绪强度 >= 3
        if emotion["intensity"] >= 3:
            return True
        
        return False
    
    def record(self, result: Dict):
        """记录到档案"""
        
        if not result["should_record"]:
            return {"status": "skipped", "reason": "not_significant"}
        
        emotion = result["emotion"]
        keywords = result["keywords"]
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        entry = f"""
### ⚡ {timestamp}
- **情绪**: {emotion['primary']} (强度: {emotion['intensity']}/5)
- **事件**: {keywords['event']}
- **来源**: {emotion['source']}
- **标签**: {', '.join(keywords['tags'])}
- **教训**: {keywords['lesson']}
- **改进**: {keywords['improvement']}
"""
        
        # 根据情绪类型写入不同档案
        if emotion["primary"] in ["成就感", "好奇", "温暖"]:
            target_file = EXPERIENCES_FILE
        else:
            target_file = FAILURES_FILE
        
        # 读取现有内容
        if target_file.exists():
            content = target_file.read_text()
        else:
            content = "# 体验档案\n"
        
        # 插入新记录
        if "---" in content:
            parts = content.split("---", 1)
            content = parts[0] + "---\n" + entry + "\n" + parts[1]
        else:
            content += entry
        
        # 写入
        target_file.write_text(content)
        
        return {"status": "recorded", "file": str(target_file)}


def main():
    import sys
    
    # 解析参数
    messages = []
    tasks = []
    input_file = None
    do_record = False
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--input" and i + 1 < len(sys.argv):
            input_file = sys.argv[i + 1]
            i += 2
        elif arg == "--messages" and i + 1 < len(sys.argv):
            try:
                messages = json.loads(sys.argv[i + 1])
            except:
                messages = []
            i += 2
        elif arg == "--tasks" and i + 1 < len(sys.argv):
            try:
                tasks = json.loads(sys.argv[i + 1])
            except:
                tasks = []
            i += 2
        elif arg == "--record":
            do_record = True
            i += 1
        else:
            i += 1
    
    # 加载输入
    if input_file and Path(input_file).exists():
        data = json.loads(Path(input_file).read_text())
        messages = data.get("messages", [])
        tasks = data.get("tasks", [])
    # else: messages and tasks already set from CLI args
    
    # 分析
    analyzer = EmotionAnalyzer()
    result = analyzer.analyze(messages, tasks)
    
    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 记录
    if do_record:
        record_result = analyzer.record(result)
        print(json.dumps(record_result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
