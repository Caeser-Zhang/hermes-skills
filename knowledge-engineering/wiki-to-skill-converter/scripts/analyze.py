#!/usr/bin/env python3
"""
Wiki → Skill 分析引擎

输入: Wiki 文本（stdin 或文件路径）
输出: JSON 分析报告

用法:
  python analyze.py wiki_content.txt
  cat wiki.md | python analyze.py -
  python analyze.py --url https://wiki.internal/k8s
"""

import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class AnalysisReport:
    type: str = "unknown"
    confidence: float = 0.0
    quality_score: int = 0
    quality_label: str = "C"
    sections_found: list = field(default_factory=list)
    keywords: list = field(default_factory=list)
    pitfall_signals: list = field(default_factory=list)
    scenarios: list = field(default_factory=list)
    word_count: int = 0
    has_code_blocks: bool = False
    warnings: list = field(default_factory=list)


# ─── 类型判定 ───────────────────────────────────────

TYPE_PATTERNS = {
    "operational": {
        "signals": [
            r"(?:症状|现象|表现|报错|异常)",
            r"(?:排查|诊断|定位|检查|调试|troubleshoot)",
            r"(?:解决|修复|处理|恢复|resolve)",
            r"(?:kubectl|systemctl|docker|ps\s+aux|top|strace)",
            r"(?:CrashLoop|Pending|NotReady|OOM|Error|Failed)",
            r"(?:第一步|第二步|步骤|step)",
            r"先.*再.*最后",
            r"(?:日志|log|trace|error\s+message)",
        ],
    },
    "advisory": {
        "signals": [
            r"(?:最佳实践|推荐|建议|规范|准则|convention)",
            r"(?:应该|不应|避免|不要|千万别|always|never)",
            r"(?::heavy_check_mark:|:x:|✅|❌|👍|👎)",
            r"(?:正确.*示例|错误.*示例|反模式|anti.?pattern)",
            r"(?:原则|principle|rule of thumb)",
            r"(?:好.*例|坏.*例|good.*bad)",
        ],
    },
    "review": {
        "signals": [
            r"(?:检查|审计|审查|合规|checklist|audit)",
            r"(?:漏洞|风险|威胁|攻击|vulnerability|risk)",
            r"(?:CVE|OWASP|SOC2|ISO\s*27001|PCI)",
            r"(?:安全|security|权限|permission)",
            r"(?:自检|自查|验证清单|verification)",
            r"(?:评分|等级|严重|critical|high|medium|low)",
        ],
    },
    "reference": {
        "signals": [
            r"(?:命令|参数|选项|flags|command)",
            r"(?:速查|参考|手册|cheatsheet|quick.?ref)",
            r"(?:CLI|API|config|配置项|setting)",
            r"(?:用法|usage|语法|syntax)",
            r"(?:默认值|可选值|取值范围)",
        ],
    },
    "context": {
        "signals": [
            r"(?:ADR|决策|架构|设计|architecture)",
            r"(?:为什么|原因|背景|动机|rationale)",
            r"(?:选择|取舍|权衡|trade.?off)",
            r"(?:前提|假设|约束|约束条件|constraint)",
            r"(?:后果|影响|implication|consequence)",
            r"(?:演进|变更|迁移|migration)",
        ],
    },
}


def determine_type(text: str) -> tuple[str, float, dict]:
    """判定 Skill 类型，返回 (类型, 置信度, 得分详情)"""
    scores = {}
    details = {}

    for tname, config in TYPE_PATTERNS.items():
        score = 0
        matches = []
        for pattern in config["signals"]:
            found = re.findall(pattern, text, re.IGNORECASE)
            if found:
                score += len(found)
                matches.append({"pattern": pattern, "count": len(found)})
        scores[tname] = score
        details[tname] = {"raw_score": score, "matches": matches}

    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]

    # 置信度计算
    if best_score == 0:
        return "operational", 0.3, details  # 默认回退

    total = sum(scores.values()) or 1
    confidence = best_score / total
    # 如果最高分不够突出，降低置信度
    runner_up = sorted(scores.values(), reverse=True)[1] if len(scores) > 1 else 0
    if runner_up > 0 and best_score / (runner_up + 1) < 2:
        confidence *= 0.6

    return best_type, min(confidence, 0.95), details


# ─── 质量评估 ───────────────────────────────────────

QUALITY_PATTERNS = {
    "symptom": [r"症状|现象|表现|报错|异常|symptom"],
    "diagnosis": [r"排查|诊断|定位|检查|调试|diagnos"],
    "resolution": [r"解决|修复|处理|恢复|resolve|fix"],
    "verification": [r"验证|确认|检查|verify|confirm|测试"],
    "pitfalls": [r"注意|小心|警告|⚠️|warning|踩.*坑|陷阱"],
    "commands": [r"```(?:bash|sh|shell|yaml|python|json)"],
    "examples": [r"示例|例子|example|比如|例如"],
}


def assess_quality(text: str) -> tuple[int, str, list]:
    """评估 Wiki 质量，返回 (0-100 分数, A/B/C 标签, 发现的章节列表)"""
    scores = {}
    sections_found = []

    for section, patterns in QUALITY_PATTERNS.items():
        found = False
        for p in patterns:
            if re.search(p, text, re.IGNORECASE):
                found = True
                break
        scores[section] = 100 if found else 0
        if found:
            sections_found.append(section)

    # 加权：诊断路径比命令示例重要
    weights = {
        "symptom": 0.20,
        "diagnosis": 0.30,
        "resolution": 0.20,
        "verification": 0.10,
        "pitfalls": 0.10,
        "commands": 0.05,
        "examples": 0.05,
    }

    quality = int(sum(scores[k] * weights[k] for k in weights))

    if quality >= 70:
        label = "A"
    elif quality >= 40:
        label = "B"
    else:
        label = "C"

    return quality, label, sections_found


# ─── 关键词提取 ─────────────────────────────────────

def extract_keywords(text: str, min_length: int = 2, max_keywords: int = 10) -> list:
    """从文本中提取触发关键词"""
    # 提取标题行
    titles = re.findall(r"^#{1,3}\s+(.+)$", text, re.MULTILINE)

    # 提取技术术语（驼峰、下划线、特定格式）
    tech_terms = set()
    tech_patterns = [
        r"\b([A-Z][a-z]+(?:[A-Z][a-z]+)+)",  # CamelCase
        r"\b([a-z]+(?:[A-Z][a-z]+)+)",        # lowerCamelCase
        r"\b([A-Z]+_[A-Z]+)",                   # CONSTANT_CASE
        r"\b(kubectl|docker|systemctl|git|curl|helm|ansible)\b",
        r"\b(CrashLoop|Pending|NotReady|OOM|Error)\b",
        r"\b([a-z-]+)\s+(?:排查|故障|优化|配置|调优)\b",
    ]
    for pattern in tech_patterns:
        for m in re.finditer(pattern, text):
            term = m.group(1).strip()
            if len(term) >= min_length:
                tech_terms.add(term)

    keywords = list(tech_terms)[:max_keywords]

    # 混合标题中的关键词
    for title in titles:
        for key in title.split():
            key = key.strip("#*[]()|`").strip()
            if len(key) >= min_length and key not in keywords:
                keywords.append(key)
                if len(keywords) >= max_keywords:
                    break

    return keywords[:max_keywords]


# ─── Pitfalls 信号提取 ──────────────────────────────

PITFALL_SIGNALS = [
    "注意", "小心", "⚠️", "踩.*坑", "教训",
    "实际上", "其实", "误区", "常见误解",
    "不要", "避免", "千万别", "禁止",
    "warning", "caution", "pitfall", "gotcha",
    "以为", "误以为", "很多人以为",
]


def extract_pitfall_signals(text: str) -> list:
    """从文本中提取 Pitfalls 信号词"""
    signals = []
    for signal in PITFALL_SIGNALS:
        for m in re.finditer(signal, text, re.IGNORECASE):
            start = max(0, m.start() - 50)
            end = min(len(text), m.end() + 100)
            context = text[start:end].strip()
            signals.append({
                "signal": signal,
                "context": context[:120] + ("..." if len(context) > 120 else ""),
            })
        if len(signals) >= 15:
            break
    return signals[:15]


# ─── 场景识别 ───────────────────────────────────────

def extract_scenarios(text: str) -> list:
    """识别 Wiki 中描述的多个问题场景"""
    scenarios = []

    # 按标题分节
    sections = re.split(r"\n(?=#{1,3}\s+)", text)

    for section in sections:
        title_match = re.match(r"^#{1,3}\s+(.+)", section)
        if not title_match:
            continue
        title = title_match.group(1).strip()
        # 跳过非问题类的标题
        skip_words = ["目录", "参考", "附录", "总结", "概述", "intro"]
        if any(w in title.lower() for w in skip_words):
            continue

        # 评估完整性
        has_symptom = bool(re.search(r"症状|现象|表现|报错|异常", section, re.IGNORECASE))
        has_diagnosis = bool(re.search(r"排查|诊断|检查|步骤", section, re.IGNORECASE))
        has_resolution = bool(re.search(r"解决|修复|处理", section, re.IGNORECASE))

        completeness = (has_symptom * 0.3 + has_diagnosis * 0.4 + has_resolution * 0.3)

        scenarios.append({
            "name": title,
            "completeness": round(completeness, 1),
        })

    return scenarios


# ─── 主流程 ─────────────────────────────────────────

def analyze(text: str) -> AnalysisReport:
    """完整分析流程"""
    report = AnalysisReport()

    if not text.strip():
        report.warnings.append("输入内容为空")
        return report

    report.word_count = len(text.split())
    report.has_code_blocks = bool(re.search(r"```", text))

    # 类型判定
    skill_type, confidence, type_details = determine_type(text)
    report.type = skill_type
    report.confidence = round(confidence, 2)

    # 质量评估
    quality, label, sections = assess_quality(text)
    report.quality_score = quality
    report.quality_label = label
    report.sections_found = sections

    # 关键词
    report.keywords = extract_keywords(text)

    # Pitfalls
    report.pitfall_signals = extract_pitfall_signals(text)

    # 场景
    report.scenarios = extract_scenarios(text)

    # 警告
    if quality < 40:
        report.warnings.append("Wiki 质量过低 (<40%)，建议轻量转化 (C级)")
    if not report.keywords:
        report.warnings.append("未能提取有效关键词，可能需要人工补充")
    if report.confidence < 0.5:
        report.warnings.append(f"类型判定置信度较低 ({report.confidence:.0%})，建议人工确认")
    if report.word_count < 50:
        report.warnings.append("Wiki 内容过短 (<50 词)，信息量不足")

    return report


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("Usage: python analyze.py <wiki_file>")
        print("       cat wiki.md | python analyze.py -")
        sys.exit(0)

    if sys.argv[1] == "-":
        text = sys.stdin.read()
    else:
        with open(sys.argv[1], encoding="utf-8") as f:
            text = f.read()

    report = analyze(text)
    output = asdict(report)

    # 美化输出
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
