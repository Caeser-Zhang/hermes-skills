#!/usr/bin/env python3
"""
Wiki → Skill 生成引擎

根据分析报告渲染对应的 Skill 模板，生成完整文件集。

用法:
  python generate.py analysis.json --type operational --name k8s-crashloop --output /tmp/skill-out/
  python generate.py analysis.json --name my-skill --output ./output/  (自动从分析报告读取类型)
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


# ─── 默认配置 ───────────────────────────────────────

DEFAULT_LIFECYCLE = {
    "review_cadence": "every_6_months",
    "last_reviewed_on": datetime.now().strftime("%Y-%m-%d"),
    "next_review_due": "",  # 自动计算
    "deprecation_criteria": [
        {"metric": "last_used_30d", "threshold": "< 3"},
        {"metric": "error_rate", "threshold": "> 40%"},
        {"metric": "stale_days", "threshold": "> 365"},
    ],
}

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")


# ─── YAML 格式化辅助 ──────────────────────────────

def format_keywords_yaml(keywords: list) -> str:
    if not keywords:
        return "        - \"fallback-keyword\""
    return "\n".join(f'        - "{kw}"' for kw in keywords[:10])


def format_tags_yaml(tags: list) -> str:
    if not tags:
        return "      - \"auto-generated\""
    return "\n".join(f'      - "{tag}"' for tag in tags)


# ─── 模板渲染（简化版 Jinja2） ─────────────────────

def render_template(template_str: str, context: dict) -> str:
    """简单的模板渲染，支持 {{var}} 和 {% for %} / {% if %}"""

    # 处理 {% for item in list %} ... {% endfor %}
    def replace_for(match):
        var = match.group(1).strip()
        lst_name = match.group(2).strip()
        body = match.group(3)
        lst = context.get(lst_name, [])
        if not lst:
            return ""
        result = []
        for item in lst:
            item_ctx = context.copy()
            if isinstance(item, dict):
                item_ctx.update(item)
            else:
                item_ctx[var] = item
            result.append(resolve_vars(body, item_ctx))
        return "\n".join(result)

    template_str = re.sub(
        r"\{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%\}(.*?)\{%\s*endfor\s*%\}",
        replace_for,
        template_str,
        flags=re.DOTALL,
    )

    # 处理 {% if var %} ... {% endif %}
    def replace_if(match):
        cond = match.group(1).strip()
        body = match.group(2)
        val = context.get(cond, False)
        if val:
            return resolve_vars(body, context)
        return ""

    template_str = re.sub(
        r"\{%\s*if\s+(\w+)\s*%\}(.*?)\{%\s*endif\s*%\}",
        replace_if,
        template_str,
        flags=re.DOTALL,
    )

    return resolve_vars(template_str, context)


def resolve_vars(text: str, context: dict) -> str:
    """替换 {{var}} 变量"""
    def replacer(match):
        key = match.group(1).strip()
        val = context.get(key, f"{{{{{key}}}}}")
        if isinstance(val, bool):
            return "true" if val else "false"
        if isinstance(val, list):
            return "\n".join(f"  - \"{item}\"" for item in val)
        if isinstance(val, dict):
            return json.dumps(val, ensure_ascii=False, indent=2)
        return str(val)
    return re.sub(r"\{\{\s*(\w+)\s*\}\}", replacer, text)


# ─── Skill 类型模板 ─────────────────────────────────
def load_template(template_type: str) -> str:
    """从 .j2 文件加载模板"""
    template_file = os.path.join(TEMPLATE_DIR, f"{template_type}.j2")
    if not Path(template_file).exists():
        raise FileNotFoundError(f"Template not found: {template_file}")
    with open(template_file, encoding="utf-8") as f:
        return f.read()
    if not tags:
        return "      - \"auto-generated\""
    return "\n".join(f'      - "{tag}"' for tag in tags)


def format_yaml_list(items: list) -> str:
    if not items:
        return "[]"
    return "\n".join(f"  - \"{item}\"" for item in items)


# ─── 默认 Pitfalls 生成（反向推导） ────────────────

def generate_default_pitfalls(skill_type: str, scenarios: list) -> str:
    """基于 Skill 类型生成默认 Pitfalls 模板"""
    defaults = {
        "operational": [
            "1. **[错误做法]** → **[为什么错]** → **[正确做法]**",
            "2. **[错误做法]** → **[为什么错]** → **[正确做法]**",
        ],
        "advisory": [
            "1. **[常见误区]** → **[为什么是误区]** → **[正确理解]**",
            "2. **[常见误区]** → **[为什么是误区]** → **[正确理解]**",
        ],
        "review": [
            "1. **[常见疏漏]** → **[为什么容易被忽略]** → **[如何避免]**",
            "2. **[常见疏漏]** → **[为什么容易被忽略]** → **[如何避免]**",
        ],
        "reference": [
            "1. **[容易混淆的参数]** → **[区别是什么]** → **[何时用哪个]**",
        ],
        "context": [
            "1. **[常见误解]** → **[为什么是误解]** → **[正确理解]**",
        ],
    }

    items = defaults.get(skill_type, defaults["operational"])

    if scenarios and len(scenarios) > 1:
        items.insert(0, "> ⚠️ 本 Skill 覆盖了多个场景，请注意使用正确的分支。")

    return "\n".join(items)


# ─── 生成动作定义 ───────────────────────────────────

def generate_actions_yaml(skill_type: str, content: dict) -> str:
    """生成 actions.yaml 骨架"""
    return f"""# Agent 可执行动作定义
# 按 body.md 诊断步骤一一对应

actions:
  - id: "first_step"
    description: "<第一步动作描述>"
    command: "<command_template>"
    executor: "shell"
    timeout_seconds: 30
    idempotent: true
    risk_level: "safe"
    
    error_handling:
      on_permission_denied: "ask_user_for_credentials"
      on_timeout: "retry_once"
    
    output_parsing:
      extract:
        - pattern: "<regex_pattern>"
          assign_to: "<variable_name>"
    
    next_action_rule:
      - condition: "<condition>"
        goto: "<next_action_id>"
      - default: "<fallback_action_id>"

  - id: "second_step"
    description: "<第二步动作描述>"
    command: "<command_template>"
    executor: "shell"
    timeout_seconds: 30
    idempotent: true
    risk_level: "safe"

  - id: "fix_action"
    description: "<修复操作描述>"
    command: "<fix_command>"
    executor: "shell"
    risk_level: "dangerous"
    requires_confirmation: true
    confirmation_message: "即将执行修复操作，确认？"
    rollback_command: "<rollback_command>"
"""


def generate_cognition_yaml(skill_type: str) -> str:
    """生成 cognition.yaml 骨架"""
    return f"""# 认知模型 — Agent 推理框架

cognition:
  type: "{skill_type}"
  
  reasoning_chain: |
    当处理此 Skill 相关的任务时，推理应遵循：
    1. 首先判断：<推理步骤1>
    2. 然后考虑：<推理步骤2>
    3. 不要线性执行步骤，先形成假设再验证。
  
  hypothesis_driven: true
  
  uncertainty_handling: |
    当信息不足时，应主动向用户提问获取关键信息，而非猜测。
    推荐问题模板：
    - "<关键问题1>"
    - "<关键问题2>"
  
  interaction_protocol:
    auto_execute:
      - "所有只读操作"
    require_confirm:
      - "任何修改操作"
      - "生产环境操作"
    progress_report:
      - "每完成一个关键步骤"
    user_timeout: "5min"
    on_timeout: "summarize_findings_and_wait"
"""


# ─── 主流程 ─────────────────────────────────────────

def generate(
    analysis: dict,
    skill_name: str,
    output_dir: str,
    skill_type: str = None,
    meta: dict = None,
) -> str:
    """
    根据分析报告生成完整 Skill 文件集。
    返回输出目录路径。
    """
    skill_type = skill_type or analysis.get("type", "operational")
    output_dir = Path(output_dir) / skill_name
    output_dir.mkdir(parents=True, exist_ok=True)

    date = datetime.now().strftime("%Y-%m-%d")
    keywords = analysis.get("keywords", [])
    scenarios = analysis.get("scenarios", [])
    pitfall_signals = analysis.get("pitfall_signals", [])
    quality_label = analysis.get("quality_label", "B")

    # 构建模板上下文
    ctx = {
        "skill_name": skill_name,
        "title": meta.get("title", skill_name.replace("-", " ").title()) if meta else skill_name.replace("-", " ").title(),
        "description": meta.get("description", f"Auto-generated from Wiki. Quality: {quality_label}") if meta else f"Auto-generated from Wiki. Quality: {quality_label}",
        "tags_yaml": format_tags_yaml(meta.get("tags", ["auto-generated", f"quality-{quality_label.lower()}"]) if meta else ["auto-generated", f"quality-{quality_label.lower()}"]),
        "keywords_yaml": format_keywords_yaml(keywords),
        "urgency": "medium",
        "review_cadence": "every_6_months",
        "date": date,
        "quality_label": quality_label,
        # 通用占位符
        "symptoms": "\n".join(f"- <症状描述 {i+1}>" for i in range(max(1, len(scenarios)))),
        "pitfalls": generate_default_pitfalls(skill_type, scenarios),
        "code_lang": "bash" if skill_type == "operational" else "python",
        "context_pattern": skill_name.replace("-", ".*"),
        "principles": "\n".join(f"{i+1}. **<原则{i+1}>** — <一句话说明>" for i in range(3)),
        "principle_name": "<原则名称>",
        "good_example": "<correct_code>",
        "bad_example": "<wrong_code>",
        "why_good": "<原因>",
        "why_bad": "<原因>",
        "exception_1": "<例外条件1>",
        "exception_2": "<例外条件2>",
        "problem": "<问题背景描述>",
        "decision": "<决策内容>",
        "constraint_1": "<约束条件1>",
        "constraint_2": "<约束条件2>",
        "pro_1": "<正面影响>",
        "con_1": "<负面影响>",
    }

    # 选择模板
    template = load_template(skill_type)

    # 渲染 body.md
    body_content = render_template(template, ctx)

    # 写入文件
    # 1. skill.yaml (嵌入在 body.md 的 frontmatter 中，这里直接写入完整 body.md)
    with open(output_dir / "body.md", "w", encoding="utf-8") as f:
        f.write(body_content)

    # 2. actions.yaml
    with open(output_dir / "actions.yaml", "w", encoding="utf-8") as f:
        f.write(generate_actions_yaml(skill_type, ctx))

    # 3. cognition.yaml
    with open(output_dir / "cognition.yaml", "w", encoding="utf-8") as f:
        f.write(generate_cognition_yaml(skill_type))

    # 4. 创建子目录
    (output_dir / "templates").mkdir(exist_ok=True)
    (output_dir / "scripts").mkdir(exist_ok=True)
    (output_dir / "references").mkdir(exist_ok=True)
    (output_dir / "examples").mkdir(exist_ok=True)

    # 5. 写入 .gitkeep
    for subdir in ["templates", "scripts", "references", "examples"]:
        (output_dir / subdir / ".gitkeep").touch()

    # 6. 写入生成元信息
    with open(output_dir / ".generation.json", "w") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "generator": "wiki-to-skill-converter/1.0.0",
            "analysis": analysis,
            "context": ctx,
        }, f, ensure_ascii=False, indent=2)

    return str(output_dir)


def main():
    parser = argparse.ArgumentParser(description="Wiki → Skill 生成引擎")
    parser.add_argument("analysis_json", help="分析报告 JSON 文件路径")
    parser.add_argument("--type", "-t", choices=["operational", "advisory", "review", "reference", "context"],
                       help="Skill 类型（不指定则从分析报告自动提取）")
    parser.add_argument("--name", "-n", required=True, help="Skill 名称（如 k8s-pod-crashloop）")
    parser.add_argument("--output", "-o", required=True, help="输出目录路径")
    parser.add_argument("--title", help="Skill 标题（可选）")
    parser.add_argument("--description", help="Skill 描述（可选）")
    parser.add_argument("--tags", help="逗号分隔的标签列表（可选）")

    args = parser.parse_args()

    with open(args.analysis_json, encoding="utf-8") as f:
        analysis = json.load(f)

    meta = {}
    if args.title:
        meta["title"] = args.title
    if args.description:
        meta["description"] = args.description
    if args.tags:
        meta["tags"] = [t.strip() for t in args.tags.split(",")]

    out = generate(
        analysis=analysis,
        skill_name=args.name,
        output_dir=args.output,
        skill_type=args.type,
        meta=meta if meta else None,
    )

    print(f"✅ Skill generated at: {out}")
    print(f"   Files: {', '.join(os.listdir(out))}")


if __name__ == "__main__":
    main()
