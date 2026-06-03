# Wiki → Skill 转化方法轮 v2.0

> 来源：Agent A（信息架构师）设计 + Agent B（Skill 设计师）批判 → 融合修正
> 评分：v1.0 4.0/10 → v2.0 综合所有 19 条改进意见

---

## 流程

```
Step 0: Skill类型判定 + 模板选择
  ↓
阶段一: 信息收集与分析 (扫描→分类→筛选→优先级排序)
  ↓
阶段二: 结构提炼 (三元组 + 触发 + Pitfalls + 认知模型)
  ↓
阶段三: 双层转化 (人类可读层 + Agent可执行层)
  ↓
阶段四: 质量保证 (L1自动化 + L2同行评审 + L3推演)
  ↓
阶段五: 生命周期管理 (owner + 审查节奏 + 退役标准)
```

## Skill 类型与模板

| 类型 | 核心结构 | 触发方式 | 示例 |
|------|---------|---------|------|
| 操作型 | 决策树→分支步骤 | 事件驱动 | K8s故障排查 |
| 指导型 | 原则→示例→反模式 | 上下文匹配 | 代码规范 |
| 审查型 | 检查清单→评分 | 持续应用 | 安全审计 |
| 参考型 | 索引→速查 | 按需检索 | CLI工具指南 |
| 上下文型 | 背景→约束 | 被动检索 | ADR |

## 优先级策略

- **A级（深度）**: 高频+高影响+高质量 → 完整文件集 (~1-5工作日)
- **B级（标准）**: 中等 → Skill骨架 + @needs-enrichment
- **C级（轻量）**: 其余 → 触发条件+摘要+原始链接 (~30min)

## Pitfalls 提取

组合策略：信号词（注意/小心/踩坑）+ 反向推导（正确步骤的反面）+ 新人盲测

格式: [错误做法] → [为什么错] → [正确做法]

## Agent 可执行层 (actions.yaml)

```yaml
actions:
  - id: "describe_pod"
    command: "kubectl describe pod {{pod}} -n {{ns}}"
    error_handling:
      on_permission_denied: "ask_user_for_kubeconfig"
      on_not_found: "ask_user_to_verify_pod_name"
    output_parsing:
      extract:
        - pattern: "Exit Code:\\s*(\\d+)"
          assign_to: "exit_code"
    next_action_rule:
      - condition: "exit_code == 137"
        goto: "check_memory_limits"
```

## 渐进式加载

- L0: 触发关键词 + 描述 + 前置检查 (~200 tokens, 始终加载)
- L1: 诊断入口 + 快速分类 + 第一步 (~500 tokens, 触发后加载)
- L2: 详细分支步骤 (~1500/branch, 按需加载)
- L3: 参考文档/脚本 (外部资源, 不占上下文)

## 生命周期

```yaml
lifecycle:
  owner_team: "platform-sre"
  review_cadence: "every_6_months"
  deprecation_criteria:
    - last_used_30d < 3
    - error_rate > 40%
    - stale_days > 365
```

## 质量检查清单

- [ ] Skill类型已判定 + 用户确认
- [ ] 触发关键词 ≥3 + negative triggers
- [ ] body.md L1/L2 分层 + token预算声明
- [ ] actions.yaml ≥2 个动作 + 错误处理 + 决策跳转
- [ ] ≥2 Pitfalls（含反向推导补充）
- [ ] 无硬编码资源名称
- [ ] lifecycle 字段完整
- [ ] L1 自动Lint通过
