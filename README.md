# ai-ppt-generator

> Project overview and instructions

## 项目简介
AI PPT 生成器 - 针对现有 AI PPT 产品的痛点，专注于「已有固定模板」场景下的智能PPT生成。

核心思路：用户通过两个输入口提供内容，一个放资料/知识库，另一个放PPT模板。系统分三步完成：
1. 自动识别模板结构（封面、目录、标题页、图文位、流程图位等）
2. 分析知识库，生成PPT大纲（文字骨架 + 数据可视化建议 + 配图/附图）
3. 将内容和模板匹配合并，输出最终PPT

解决了市场现有产品忽略的最大使用场景：用户已有模板，只需要AI填充内容。

## 目录结构
```
ai-ppt-generator/
├── docs/          # 文档：PRD、架构设计、开发计划
├── src/           # 源代码
├── test/          # 测试用例和测试结果
└── memory/        # 项目独立记忆（各 agent 工作状态）
    ├── agents/    # 各 agent 的 SESSION-STATE
    ├── daily/     # 每日工作记录
    └── MEMORY.md  # 整理后的长期记忆
```

## 当前状态
- [x] 需求分析 (PM) **已完成**
- [x] 架构设计 (Arch) **已完成**
- [x] 开发 (Codex) **已完成**
- [x] 代码评审 (Review) **已完成**
- [x] 测试 (Test) **已完成**
- [x] **完成 ✅**

## 备注
[Any additional notes]
