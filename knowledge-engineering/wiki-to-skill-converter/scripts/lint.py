#!/usr/bin/env python3
"""
Skill 自动验证引擎

检查生成的 Skill 文件集的完整性、规范性和正确性。

用法:
  python lint.py <skill_directory>
  python lint.py --json <skill_directory>   # JSON 输出
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional


# ─── 检查结果类型 ──────────────────────────────────

class Issue:
    def __init__(self, severity: str, check: str, msg: str, fix: str = ""):
        self.severity = severity  # error, warn, info
        self.check = check
        self.msg = msg
        self.fix = fix

    def to_dict(self):
        return {"severity": self.severity, "check": self.check, "msg": self.msg, "fix": self.fix}

    def __repr__(self):
        icon = {"error": "❌", "warn": "⚠️", "info": "ℹ️"}[self.severity]
        s = f"{icon} [{self.check}] {self.msg}"
        if self.fix:
            s += f"\n   💡 {self.fix}"
        return s


# ─── 检查器 ────────────────────────────────────────

def check_file_structure(skill_dir: Path) -> list[Issue]:
    """检查文件结构完整性"""
    issues = []
    required = ["body.md", "actions.yaml", "cognition.yaml"]

    for f in required:
        if not (skill_dir / f).exists():
            issues.append(Issue("error", "structure", f"缺少核心文件: {f}",
                               f"运行 generate.py 重新生成，确保包含 {f}"))

    recommended_dirs = ["templates", "scripts", "references", "examples"]
    for d in recommended_dirs:
        if not (skill_dir / d).is_dir():
            issues.append(Issue("warn", "structure", f"缺少推荐目录: {d}/",
                               f"创建 mkdir -p {skill_dir / d}"))

    return issues


def check_body_md(skill_dir: Path) -> list[Issue]:
    """检查 body.md 内容规范"""
    issues = []
    body_path = skill_dir / "body.md"
    if not body_path.exists():
        return issues

    content = body_path.read_text(encoding="utf-8")

    # 检查渐进式加载声明
    if "@load_strategy" not in content:
        issues.append(Issue("warn", "body", "缺少 @load_strategy 声明",
                           "在 body.md 顶部 HTML 注释中添加加载策略"))

    if "@l1_tokens" not in content and "L1:" not in content:
        issues.append(Issue("warn", "body", "缺少 L1 层级标注",
                           "添加 <!-- @l1_tokens: ~500 --> 和 ## L1: 章节"))

    # 检查 Pitfalls
    if not re.search(r"(Pitfalls|陷阱|常见问题|⚠️|注意事项)", content):
        issues.append(Issue("warn", "body", "缺少 Pitfalls 部分",
                           "添加 ## ⚠️ 常见陷阱 章节"))

    # 检查验证步骤
    if not re.search(r"(验证|verify|确认.*修|检查清单)", content):
        issues.append(Issue("warn", "body", "缺少验证步骤",
                           "添加 ## ✅ 验证清单 章节"))

    # 检查硬编码资源名（危险信号）
    hardcoded_patterns = [
        (r'kubectl\s+\w+\s+(?!<\w+>|\$\w+|\$\{)[a-z0-9-]{8,}', "疑似硬编码资源名称"),
        (r'(namespace|ns)\s+(?!<\w+>|\$\w+|\$\{)\w{4,}', "疑似硬编码 namespace"),
    ]
    for pattern, desc in hardcoded_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            issues.append(Issue("warn", "body", f"{desc}: {matches[0][:50]}",
                               "用 <placeholder> 或 $VARIABLE 替代具体名称"))

    # 检查命令块
    code_blocks = re.findall(r"```(?:bash|sh|shell)\n(.*?)```", content, re.DOTALL)
    for i, block in enumerate(code_blocks):
        block = block.strip()
        if not block:
            continue
        # 检查危险操作
        dangerous = ["--force", "--grace-period=0", "rm -rf /", "DROP TABLE", "TRUNCATE"]
        for d in dangerous:
            if d in block:
                if "危险" not in content[max(0, content.index(block)-200):content.index(block)]:
                    issues.append(Issue("error", "body", f"命令块 #{i+1} 含危险操作 '{d}'，但缺少安全标注",
                                       "添加注释说明操作风险和适用条件"))

    return issues


def check_actions_yaml(skill_dir: Path) -> list[Issue]:
    """检查 actions.yaml"""
    issues = []
    actions_path = skill_dir / "actions.yaml"
    if not actions_path.exists():
        return [Issue("error", "actions", "缺少 actions.yaml")]

    content = actions_path.read_text(encoding="utf-8")

    # 检查最少动作数
    action_count = len(re.findall(r"^\s*- id:", content, re.MULTILINE))
    if action_count < 2:
        issues.append(Issue("error", "actions", f"actions.yaml 仅包含 {action_count} 个动作 (<2)",
                           "至少定义 2 个可执行动作"))

    # 检查是否有错误处理
    if "error_handling" not in content and "on_permission" not in content:
        issues.append(Issue("warn", "actions", "缺少 error_handling 定义",
                           "为每个 action 添加 on_permission_denied 等错误处理"))

    # 检查是否有回滚
    has_dangerous = "dangerous" in content or "requires_confirmation" in content
    has_rollback = "rollback_command" in content
    if has_dangerous and not has_rollback:
        issues.append(Issue("warn", "actions", "存在危险操作但缺少 rollback_command",
                           "为标记 dangerous 的 action 添加回滚命令"))

    return issues


def check_cognition_yaml(skill_dir: Path) -> list[Issue]:
    """检查 cognition.yaml"""
    issues = []
    cog_path = skill_dir / "cognition.yaml"
    if not cog_path.exists():
        return [Issue("error", "cognition", "缺少 cognition.yaml")]

    content = cog_path.read_text(encoding="utf-8")

    if "reasoning_chain" not in content:
        issues.append(Issue("warn", "cognition", "缺少 reasoning_chain",
                           "添加推理链指导 Agent 如何思考"))

    if "interaction_protocol" not in content:
        issues.append(Issue("warn", "cognition", "缺少 interaction_protocol",
                           "定义 auto_execute 和 require_confirm 操作"))

    return issues


def check_skill_yaml(skill_dir: Path) -> list[Issue]:
    """检查 skill.yaml（如果存在独立文件）"""
    # skill.yaml 可能内嵌在 body.md frontmatter 中
    # 这里检查独立的 skill.yaml 文件
    issues = []
    yaml_path = skill_dir / "skill.yaml"

    if not yaml_path.exists():
        # 检查 body.md frontmatter
        body_path = skill_dir / "body.md"
        if body_path.exists():
            content = body_path.read_text(encoding="utf-8")
            if not content.startswith("---"):
                issues.append(Issue("warn", "skill.yaml", "body.md 缺少 YAML frontmatter",
                                   "在 body.md 顶部添加 --- 包裹的元数据"))
        return issues

    content = yaml_path.read_text(encoding="utf-8")

    # 关键词检查
    kw_match = re.findall(r'keywords:\s*\n((?:\s*- .+\n?)+)', content)
    if kw_match:
        kw_block = kw_match[0]
        kw_count = len(re.findall(r"^\s*-\s+", kw_block, re.MULTILINE))
        if kw_count < 3:
            issues.append(Issue("warn", "skill.yaml", f"触发关键词仅 {kw_count} 个 (<3)",
                               "添加更多触发关键词以提高匹配率"))
    else:
        issues.append(Issue("error", "skill.yaml", "缺少 keywords 字段"))

    # 生命周期检查
    if "lifecycle" not in content:
        issues.append(Issue("warn", "skill.yaml", "缺少 lifecycle 配置",
                           "添加 review_cadence 和 deprecation_criteria"))
    elif "review_cadence" not in content:
        issues.append(Issue("warn", "skill.yaml", "lifecycle 缺少 review_cadence",
                           "设置 review_cadence: 'every_6_months'"))

    # 冲突解决
    if "conflict_resolution" not in content:
        issues.append(Issue("info", "skill.yaml", "缺少 conflict_resolution（非必须，但推荐）",
                           "添加 priority 值避免多 Skill 冲突时选择困难"))

    # 负面触发
    if "negative_triggers" not in content:
        issues.append(Issue("info", "skill.yaml", "缺少 negative_triggers（非必须，但推荐）",
                           "添加误触发场景的排除规则"))

    return issues


def check_references(skill_dir: Path) -> list[Issue]:
    """检查引用完整性"""
    issues = []
    body_path = skill_dir / "body.md"
    if not body_path.exists():
        return issues

    content = body_path.read_text(encoding="utf-8")

    # 检查 @ref:, @see:, @include: 引用
    refs = re.findall(r"@(?:ref|see|include|branch):\s*(\S+)", content)
    for ref in refs:
        # 跳过模板 placeholder (<xxx>)
        if ref.startswith("<") and ref.endswith(">"):
            continue
        ref_path = skill_dir / ref.lstrip("/")
        if not ref_path.exists() and not ref.startswith("http"):
            issues.append(Issue("warn", "refs", f"引用路径不存在: {ref}",
                               "检查文件路径或创建对应文件"))

    # 检查外部链接
    urls = re.findall(r"https?://[^\s)]+", content)
    # 不实际发起 HTTP 请求，仅检查格式
    for url in urls:
        if len(url) > 200:
            issues.append(Issue("info", "refs", f"外部链接过长: {url[:80]}..."))

    return issues


# ─── 主流程 ─────────────────────────────────────────

def lint(skill_dir: str) -> dict:
    """运行所有检查"""
    skill_dir = Path(skill_dir).resolve()

    if not skill_dir.is_dir():
        return {"error": f"目录不存在: {skill_dir}", "issues": []}

    all_issues = []
    checks = [
        ("文件结构", check_file_structure),
        ("body.md", check_body_md),
        ("actions.yaml", check_actions_yaml),
        ("cognition.yaml", check_cognition_yaml),
        ("skill.yaml", check_skill_yaml),
        ("引用完整性", check_references),
    ]

    for check_name, check_fn in checks:
        issues = check_fn(skill_dir)
        for issue in issues:
            issue.check = check_name
        all_issues.extend(issues)

    error_count = sum(1 for i in all_issues if i.severity == "error")
    warn_count = sum(1 for i in all_issues if i.severity == "warn")
    info_count = sum(1 for i in all_issues if i.severity == "info")

    return {
        "skill_dir": str(skill_dir),
        "passed": error_count == 0,
        "summary": {"error": error_count, "warn": warn_count, "info": info_count, "total": len(all_issues)},
        "issues": [i.to_dict() for i in all_issues],
    }


def main():
    parser = argparse.ArgumentParser(description="Skill 自动验证引擎")
    parser.add_argument("skill_dir", help="Skill 目录路径")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    args = parser.parse_args()

    result = lint(args.skill_dir)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if "error" in result:
            print(f"❌ {result['error']}")
            sys.exit(1)

        s = result["summary"]
        print(f"\n📋 Lint Report: {result['skill_dir']}")
        print(f"   {s['error']} errors, {s['warn']} warnings, {s['info']} info\n")

        for issue in result["issues"]:
            print(f"   {Issue(**issue)}")

        if result["passed"]:
            print(f"\n✅ All checks passed!")
        else:
            print(f"\n❌ {s['error']} errors need to be fixed.")
            sys.exit(1)


if __name__ == "__main__":
    main()
