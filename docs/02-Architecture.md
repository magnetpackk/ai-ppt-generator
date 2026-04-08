# Architecture Design - ai-ppt-generator

> 架构设计文档

## 1. 架构概览

整体采用模块化分层设计，四个核心阶段完全解耦，可独立迭代优化：

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                         │
├─────────────────────────────────────────────────────────────┤
│  文件上传 → 识别结果预览确认 → 大纲确认 → 下载生成结果       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     模块一：Template Parser                   │
│                     (PPT模板结构解析)                        │
├─────────────────────────────────────────────────────────────┤
│ 输入：.pptx 模板文件                                         │
│ 输出：TemplateStructure 结构定义                            │
│  - pages[]: 每页的类型(封面|目录|标题|正文)                  │
│  - placeholders[]: 每个占位区域的位置、类型(文字|图片|图表)  │
│  - 原始样式信息：主题、字体、配色                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     模块二：Content Organizer                 │
│                     (知识库内容整理)                          │
├─────────────────────────────────────────────────────────────┤
│ 输入：用户资料文档 + TemplateStructure                       │
│ 输出：ContentPlan 内容规划                                  │
│  - outline[]: 每页的文字内容大纲                              │
│  - dataBlocks[]: 数据块 -> 推荐可视化类型                    │
│  - imageRequests[]: 图片需求 -> 来源(已有|搜索|生成)         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     模块三：ImageHandler                      │
│                     (图片处理：搜索/生成)                     │
├─────────────────────────────────────────────────────────────┤
│ 输入：imageRequests[]                                        │
│ 输出：ImageResult[] -> url 或 base64                          │
│  优先级策略：用户已有 > 联网搜索 > AI生成                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     模块四：PPT Compositor                    │
│                     (内容模板合并生成)                        │
├─────────────────────────────────────────────────────────────┤
│ 输入：原始模板 + TemplateStructure + ContentPlan + Images   │
│ 输出：最终 .pptx 文件                                         │
│  - 保持原有样式，只替换内容                                  │
│  - 自动文字大小适配                                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      输出下载                                 │
└─────────────────────────────────────────────────────────────┘
```

## 1.1 技术选型
| 层级 | 技术方案 | 选型理由 |
|------|----------|----------|
| **PPT 文件操作** | python-pptx | Python 生态最成熟的 .pptx 读写库，支持保留样式 |
| **模板结构识别** | GPT-4o / Claude 3.5 Sonnet + OCR | 通过 AI 理解幻灯片内容和布局，判断页面类型和占位区域 |
| **内容整理提炼** | GPT-4o / Claude 3.5 Sonnet | LLM 天然擅长文档内容提炼和大纲整理 |
| **数据可视化推荐** | LLM + 规则匹配 | LLM 判断数据类型，规则映射到合适图表 |
| **图片搜索** | 必应图片搜索 API / Google Custom Search | 稳定的公开图片搜索接口 |
| **AI 图片生成** | DALL·E 3 / Midjourney API / Stable Diffusion | 按需生成示意图 |
| **后端框架** | FastAPI | 轻量、快速、异步支持，适合AI服务 |
| **前端框架** | React / Next.js | 成熟的SPA框架，开发效率高 |
| **存储** | 临时存储 + Redis (可选) | 文件处理完即可下载，不需要长期存储，降低存储成本 |

## 1.2 架构特点

1. **模块化解耦**：四个核心模块完全独立，可以单独替换优化
   - 比如模板解析不准，可以单独换更好的 AI 模型
   - 图片搜索不满意，可以换搜索源不影响其他模块

2. **AI 优先**：依赖大语言模型理解能力，不是规则硬编码
   - 模板结构识别靠 AI 看布局，比规则更灵活适应各种模板
   - 内容整理靠 AI 提炼，比抽取式摘要质量更高

3. **渐进式交付**：每个阶段都可以给用户确认，错了可以人工纠正
   - 模板识别结果可以预览修正
   - 内容大纲可以调整后再生成

## 2. 模块详细设计

### 2.1 模块一：Template Parser (模板解析)

**职责：**
- 读取 .pptx 文件，提取每页的形状、文本框、图片框位置
- 调用 AI 分析每页的类型和每个占位区域的用途
- 保留原始主题、字体、配色信息

**输入：**
```typescript
interface ParseTemplateInput {
  templateFile: Buffer; // .pptx 文件二进制
}
```

**输出：**
```typescript
interface TemplateStructure {
  slideCount: number;
  slides: SlideInfo[];
  theme: ThemeInfo;
}

interface SlideInfo {
  index: number;
  pageType: 'cover' | 'toc' | 'title' | 'content' | 'section' | 'blank';
  placeholders: Placeholder[];
}

interface Placeholder {
  shapeId: number;
  type: 'text' | 'image' | 'chart' | 'table' | 'diagram';
  boundingBox: {x: number, y: number, w: number, h: number};
  expectedTextLength?: number; // 预估适合放多少文字
}

interface ThemeInfo {
  backgroundColor: string;
  fontFamily: string;
  colorScheme: string[];
}
```

**AI 提示词策略：**
- 将幻灯片渲染为图片，给 GPT-4o 看："这是PPT模板的一页，请分析这是什么类型的页面，每个框应该放什么内容"
- 输出结构化 JSON 匹配上面的接口

### 2.2 模块二：Content Organizer (内容整理)

**职责：**
- 读取用户上传的资料文档，提取全文
- 根据模板页数和结构，把内容分配到对应页面
- 识别数据块，推荐可视化类型
- 识别需要图片的位置，生成图片搜索关键词

**输入：**
```typescript
interface OrganizeContentInput {
  sourceDocuments: Buffer[]; // PDF/Word/TXT
  templateStructure: TemplateStructure;
}
```

**输出：**
```typescript
interface ContentPlan {
  pages: ContentPage[];
  dataBlocks: DataBlock[];
  imageRequests: ImageRequest[];
}

interface ContentPage {
  slideIndex: number;
  pageType: string;
  content: string; // 整理后的文字内容
}

interface DataBlock {
  slideIndex: number;
  placeholderId: number;
  rawData: string;
  structuredData: TableData | ChartData;
  recommendedType: 'table' | 'bar' | 'line' | 'pie' | 'scatter';
  title: string;
}

interface ImageRequest {
  slideIndex: number;
  placeholderId: number;
  keywords: string[];
  priority: 'user-provided' | 'search' | 'generate';
  description: string;
}
```

### 2.3 模块三：ImageHandler (图片处理)

**职责：**
- 按优先级处理每个图片需求
- 用户知识库已有 → 直接使用
- 没有 → 联网搜索相关图片
- 搜索不到 → 调用 AI 生成

**优先级策略：**
1. **用户提供**：从用户上传资料中提取相关图片 → 最快，质量可控
2. **联网搜索**：从网上找合适的图片 → 覆盖大部分场景
3. **AI 生成**：搜索不到时，根据描述生成 → 保底方案

### 2.4 模块四：PPT Compositor (合并生成)

**职责：**
- 读取原始模板
- 把整理好的文字填充到对应占位位置
- 插入图片到图片位置
- 根据数据推荐生成图表/表格
- 保持原有样式不变
- 输出最终 .pptx

**关键技术点：**
- 使用 python-pptx 的 `clone_shape` 保持原有样式
- 文字大小自动调整：如果内容超出占位，适当缩小字号
- 图片自动缩放适应占位框

## 3. 数据模型

核心就是前面三个接口定义：
- `TemplateStructure` - 模板解析结果
- `ContentPlan` - 内容整理结果
- `ImageResult` - 图片处理结果

模块之间只通过这几个数据结构交互，完全解耦。

## 4. 关键流程

### 4.1 完整处理流程

```
用户上传模板 + 资料
    ↓
TemplateParser.parse()
    ↓
返回识别结果给用户确认
    ↓(用户确认或修正)
ContentOrganizer.organize()
    ↓
返回内容大纲给用户确认
    ↓(用户确认或修正)
ImageHandler.processAll()
    ↓
PPTCompositor.compose()
    ↓
输出最终PPT供用户下载
```

### 4.2 用户干预点

设计了两个人工干预节点，提升准确率：
1. **模板识别后**：AI 识别不可能 100% 正确，允许用户调整纠正
2. **内容整理后**：允许用户调整内容分配，确认后再生成

## 5. 风险评估

| 风险点 | 影响程度 | 应对措施 |
|--------|----------|----------|
| 模板识别准确率不够 | 高 | 1) 提供预览确认允许人工修正 2) 迭代优化 AI 提示词 3) 后期可以训练专门的检测模型 |
| LLM 调用成本高 | 中 | 1) 对简单模板用规则预解析 2) 缓存重复结果 3) 支持用户配置自己的 API Key |
| 图片搜索版权问题 | 中 | 1) 搜索时筛选免费可商用授权 2) 提示用户需要商用自行确认 3) 默认优先 AI 生成规避版权 |
| 复杂PPT模板嵌套太多 python-pptx 处理不了 | 中 | 1) 先做兼容性测试 2) 考虑备选方案：libreoffice headless 转换 3) 文档说明支持范围 |
| 生成结果文字排版乱掉 | 中 | 1) 保留原文本框样式 2) 自动适配字号 3) 用户可导出后微调 |

## 6. 部署架构

**最小可行原型 (MVP) 部署：**
```
Next.js 全栈应用
├── Frontend: Vercel / 服务器部署
├── Backend API: FastAPI 封装处理逻辑
├── Static Files: 存储上传和生成文件（临时）
└── 调用外部 API: OpenAI / Anthropic / 图片搜索 / AI绘图
```

**可扩展后续架构：**
- 增加 Celery 异步任务队列，处理长时间生成
- 增加 Redis 缓存重复请求
- 增加用户系统和项目保存功能

---
*Created: 2026-04-07 17:44 GMT+8*
*Updated: 2026-04-07 18:05 GMT+8*
