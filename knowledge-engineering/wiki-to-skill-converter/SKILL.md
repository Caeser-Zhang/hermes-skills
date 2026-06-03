---
name: wiki-to-skill-converter
description: 将团队经验Wiki（URL或粘贴文本）转化为高质量的Hermes Agent Skill。自动判定5种Skill类型、生成完整文件集（skill.yaml + body.md + actions.yaml + cognition.yaml）。三步流水线：分析→生成→Lint。包含5种类型模板和可执行Python脚本。
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [knowledge-engineering, wiki, automation, meta-skill, skill-creation]
    triggers:
      keywords:
        - "Wiki转Skill"
        - "经验文档转化为Skill"
        - "创建Skill"
        - "知识沉淀"
        - "把Wiki变成Skill"
        - "从文档创建skill"
        - "批量转化Wiki"
---

# Wiki → Skill Converter

> **Meta-Skill**: 用 AI 自动化经验 Wiki 到 Agent Skill 的转化。三步流水线：`analyze → generate → lint`。

## 快速开始

### 一键转化（交互模式）

直接告诉 Hermes Agent：

```
用户: 把这个Wiki转成Skill: https://wiki.internal/k8s-troubleshooting

Agent:
  📖 读取 Wiki...
  🔍 分析: 操作型, B级(72%), 3个场景
  💡 建议拆分为3个独立Skill, 确认?

用户: 先做 CrashLoop

Agent:
  ✅ 已生成 k8s-pod-crashloop/
     ├── body.md (L1+L2 渐进式加载)
     ├── actions.yaml (6个可执行动作)
     ├── cognition.yaml (推理链+交互协议)
  📋 Lint: 2个警告
```

### 命令行流水线

```bash
# Step 1: 分析 Wiki 内容
cat wiki_content.md | python scripts/analyze.py - > analysis.json

# Step 2: 查看分析结果，确认类型
python -c "import json; r=json.load(open('analysis.json')); print(f\"Type: {r['type']} ({r['confidence']:.0%})\")"

# Step 3: 生成 Skill 文件集
python scripts/generate.py analysis.json \
  --type operational \
  --name k8s-crashloop \
  --output ./skills-output/

# Step 4: 验证质量
python scripts/lint.py ./skills-output/k8s-crashloop/
```

## 工具箱

| 资源 | 功能 | 路径 |
|------|------|------|
| **analyze.py** | 类型判定 + 质量评估 + 关键词提取 | `scripts/analyze.py` |
| **generate.py** | 模板渲染 + 文件生成 | `scripts/generate.py` |
| **lint.py** | 结构 + 规范 + 引用完整性检查 | `scripts/lint.py` |
| **operational.j2** | 故障排查/部署操作模板 | `templates/operational.j2` |
| **advisory.j2** | 最佳实践/代码规范模板 | `templates/advisory.j2` |
| **review.j2** | 安全检查/合规审查模板 | `templates/review.j2` |
| **reference.j2** | 命令速查/配置参考模板 | `templates/reference.j2` |
| **context.j2** | 架构决策/设计约束模板 | `templates/context.j2` |
| **方法论 v2.0** | 完整转化方法论 | `references/methodology-v2.md` |

## 核心原理

```
Wiki (经验叙事) → 分析 → 模板匹配 → Skill (可执行指南)
```

### 三条铁律

1. **为 Agent 设计，而非仅为人设计** — 需要双层输出：body.md (人类可读) + actions.yaml (Agent 可执行)
2. **渐进式加载，而非全量灌入** — L0-L3 分层，声明 token 预算
3. **自动化边界清晰** — Agent 做结构转化，人做领域知识补充

### 不做什么

❌ 编造不存在的诊断路径（标记 @needs-enrichment）
❌ 写死具体资源名称（一律用 `<placeholder>`）
❌ 跳过人工确认直接输出最终文件

## 工作流程

### Phase 1: 分析 (Analyze)

1. **获取内容** — 通过 web_extract 读取 URL，或直接使用用户粘贴的文本
2. **运行 analyze.py** — 输出 JSON 分析报告：
   - `type`: 5 种 Skill 类型之一（operational/advisory/review/reference/context）
   - `confidence`: 置信度 (0-1)
   - `quality_score` + `quality_label`: A(≥70) / B(40-69) / C(<40)
   - `keywords`: 自动提取的触发关键词
   - `pitfall_signals`: 发现的 Pitfalls 信号词
   - `scenarios`: 识别的多个问题场景
3. **展示分析结果，请用户确认类型和拆分策略后再进入 Phase 2**

### 5 种 Skill 类型判定

| 类型 | 特征信号 | 核心结构 | 适用 |
|------|---------|---------|------|
| **operational** | 症状/排查/诊断/解决/kubectl | 决策树 + 分支步骤 | 故障排查、部署操作 |
| **advisory** | 最佳实践/推荐/规范/✅/❌ | 原则 + 示例 + 反模式 | 代码规范、最佳实践 |
| **review** | 检查/审计/合规/风险/CVE | 检查清单 + 风险矩阵 | 安全审查、合规检查 |
| **reference** | 命令/参数/速查/config/CLI | 索引 + 速查表 | 工具指南、配置参考 |
| **context** | 决策/架构/为什么/取舍/ADR | 背景 + 约束 | 架构决策、设计文档 |

### Phase 2: 生成 (Generate)

1. 用户确认 Skill 类型和拆分策略
2. **运行 generate.py** — 按选定模板渲染文件集：

```
skills/<skill-name>/
├── body.md          # 渐进式加载 (L1入口 ~500t + L2分支 按需加载)
├── actions.yaml     # Agent 可执行动作 (含错误处理 + 决策跳转)
├── cognition.yaml   # 认知模型 (推理链 + 交互协议)
├── .generation.json # 生成元信息
├── templates/       # 外挂模板 (.gitkeep)
├── scripts/         # 外挂脚本 (.gitkeep)
├── references/      # 参考文档 (.gitkeep)
└── examples/        # 案例库 (.gitkeep)
```

**生成规则**：
- 命令块标注用途 + 前置条件 + 危险等级（仅必要时）
- 参数用 `<placeholder>` 占位
- Pitfalls 用默认模板（操作型: 错误→原因→正确 格式）
- 默认 lifecycle.review_cadence = "every_6_months"
- 默认 conflict_resolution.priority = 50

### 优先级策略

| 等级 | 条件 | 处理方式 |
|------|------|---------|
| **A** | 高质量(≥70) + 高频 + 高影响 | 完整转化 → 全文件集 |
| **B** | 中等(40-69) / 中频 | 标准转化 → 标记 @needs-enrichment |
| **C** | 低质量(<40) / 低频 | 轻量转化 → 仅触发条件 + 摘要 |

### Phase 3: 审查 (Lint & Review)

1. **运行 lint.py** — 自动检查：
   - 文件结构完整性（body.md / actions.yaml / cognition.yaml）
   - body.md L1/L2 分层标注 + Pitfalls + 验证清单
   - actions.yaml 动作数 ≥2 + 错误处理 + 回滚命令
   - skill.yaml 关键词 ≥3 + lifecycle + negative_triggers
   - 引用路径有效性 + 硬编码检测
2. 展示 Lint 报告
3. 提示需人工补充：环境参数、外挂脚本内容、SME 确认

## Pitfalls

1. **[类型误判]** — 把代码规范Wiki当成操作型Skill → Phase 1 展示结果后请用户二次确认
2. **[Wiki 残缺]** — 诊断路径缺失 >50% → 标记 @needs-enrichment，不强行补全
3. **[混入一次性经验]** — "上次加节点就好了" → 识别时间/版本绑定词，仅提取通用模式
4. **[环境硬编码]** — 集群名/IP 写死 → 模板中用 `{{placeholder}}` 替换
5. **[跳过确认]** — 不要跳过 Phase 1 的类型确认步骤直接生成

## 验证清单

生成每个 Skill 后确认：
- [ ] body.md 含 @load_strategy + L1/L2 分层
- [ ] actions.yaml 含 ≥2 个可执行动作 + error_handling
- [ ] cognition.yaml 含 reasoning_chain + interaction_protocol
- [ ] 触发关键词 ≥3 且无双关
- [ ] lifecycle.review_cadence 已设置
- [ ] 引用路径全部有效
- [ ] 无具体环境信息硬编码
- [ ] 用户已确认 Skill 类型

## 生命周期

生成每个 Skill 时默认配置：

```yaml
lifecycle:
  review_cadence: "every_6_months"
  deprecation_criteria:
    - last_used_30d < 3
    - error_rate > 40%
    - stale_days > 365
```

**提醒用户设置**: owner_team, owner_contact

---

**参考**: 方法论经过两个 Agent 多轮交锋验证 — 原始方案 (v1.0) 被批判评分 4.0/10，修正后 v2.0 吸收 19 条具体改进建议。