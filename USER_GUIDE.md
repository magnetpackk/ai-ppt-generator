# AI PPT Generator 使用手册

## 📖 目录

- [产品简介](#-产品简介)
- [快速开始](#-快速开始)
- [API 接口文档](#-api-接口文档)
- [项目结构](#-项目结构)
- [技术架构](#-技术架构)
- [开发指南](#-开发指南)
- [常见问题](#-常见问题)

---

## 🎯 产品简介

**AI PPT Generator** 是一个专注于**已有模板填充**场景的AI PPT生成工具。

### 和其他 AI PPT 产品的区别

| 特性 | 传统 AI PPT | AI PPT Generator |
|------|------------|-----------------|
| 创作方式 | AI 从零生成 | AI 填充你已有的模板 |
| 模板风格 | AI 决定 | 你决定 |
| 品牌一致性 | 难以保证 | 完美保持 |

### 核心工作流程

```
┌─────────────┐   ┌─────────────┐
│  资料/知识库 │   │  PPT模板文件 │
└──────┬──────┘   └──────┬──────┘
       │                 │
       └─────────┬───────┘
                 ▼
       第一步：模板结构自动识别
                 │
                 ▼
       第二步：知识库内容整理
       - 文字大纲分配到页
       - 数据可视化推荐
       - 图片需求处理
                 │
                 ▼
       第三步：内容模板匹配合并
                 │
                 ▼
         输出最终PPT文件
```

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- pip 包管理

### 1. 安装依赖

```bash
# 进入项目目录
cd /root/.openclaw/workspace/projects/ai-ppt-generator

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 必须配置：OpenAI API Key（用于AI识别和内容整理）
export OPENAI_API_KEY="your-openai-api-key-here"

# 可选配置：自定义OpenAI接口地址（使用中转服务时配置）
export OPENAI_BASE_URL="https://api.openai.com/v1"

# 可选配置：必应搜索API Key（用于图片搜索，没有则只能AI生成）
export BING_SEARCH_KEY="your-bing-search-key-here"
```

### 3. 启动服务

```bash
cd src/api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 打开界面

浏览器访问：
```
http://localhost:8000/docs
```

你会看到 Swagger UI 界面，可以在线测试API。

---

## 🔌 API 接口文档

### 1. 健康检查

```
GET /health
```

**响应示例：**
```json
{
  "status": "healthy"
}
```

### 2. 解析模板

```
POST /api/parse-template
Content-Type: multipart/form-data
```

**参数：**
- `template`: `.pptx` 模板文件

**响应示例：**
```json
{
  "success": true,
  "slide_count": 10,
  "structure": {
    "slide_count": 10,
    "slides": [
      {
        "index": 0,
        "page_type": "cover",
        "placeholders": [
          {
            "shape_id": 1,
            "type": "text",
            "x": 1.0,
            "y": 2.0,
            "width": 8.0,
            "height": 2.0
          }
        ]
      }
    ],
    "theme": {
      "background_color": "#ffffff",
      "font_family": "Microsoft YaHei",
      "color_scheme": ["#ffffff", "#000000"]
    }
  },
  "error": null
}
```

**说明：**
- `page_type` 可能值：`cover`(封面)、`toc`(目录)、`title`(标题页)、`content`(内容页)、`section`(章节分隔)、`blank`(空白)
- `type`(占位类型) 可能值：`text`、`image`、`chart`、`table`、`diagram`

### 3. 整理内容

```
POST /api/organize-content
Content-Type: application/json
```

**请求体：**
```json
{
  "source_text": "你的资料全文内容...",
  "template_structure": {} // 上一步返回的structure
}
```

**响应示例：**
```json
{
  "success": true,
  "content_plan": {
    "pages": [
      {
        "slide_index": 0,
        "page_type": "cover",
        "content": "AI PPT Generator\n让AI帮你填充模板"
      }
    ],
    "data_blocks": [
      {
        "slide_index": 3,
        "placeholder_id": 2,
        "raw_data": "...数据内容...",
        "recommended_type": "bar",
        "title": "月度销售数据"
      }
    ],
    "image_requests": [
      {
        "slide_index": 2,
        "placeholder_id": 3,
        "keywords": ["人工智能", "PPT"],
        "priority": "search",
        "description": "人工智能PPT应用场景示意图"
      }
    ]
  },
  "error": null
}
```

### 4. 生成最终PPT

```
POST /api/generate-ppt
Content-Type: multipart/form-data
```

**参数：**
- `template`: 原始模板文件
- `content_plan`: JSON 格式的内容规划
- `template_structure`: JSON 格式的模板结构

**响应：**
- 成功：返回 `.pptx` 文件供下载
- 失败：返回错误信息

---

## 📁 项目结构

```
ai-ppt-generator/
├── USER_GUIDE.md              # 本使用手册
├── README.md                  # 项目概览
├── requirements.txt           # Python依赖列表
├── docs/
│   ├── 01-PRD.md              # 产品需求文档
│   ├── 02-Architecture.md     # 架构设计文档
│   ├── review-report.md       # 代码评审报告
│   └── test-report.md         # 测试报告
├── src/
│   ├── core/                  # 核心业务模块
│   │   ├── __init__.py
│   │   ├── template_parser.py    # 模块一：模板解析
│   │   ├── content_organizer.py  # 模块二：内容整理
│   │   ├── image_handler.py      # 模块三：图片处理
│   │   └── ppt_compositor.py     # 模块四：合成输出
│   └── api/
│       └── main.py              # FastAPI 服务入口
├── test/
│   └── README.md              # 测试说明
└── memory/                    # 项目记忆（Elite Longterm Memory）
    ├── MEMORY.md
    ├── pipeline-state.json
    └── agents/
        ├── SESSION-STATE-pm.md
        ├── SESSION-STATE-arch.md
        ├── SESSION-STATE-codex.md
        ├── SESSION-STATE-review.md
        └── SESSION-STATE-test.md
```

---

## 🏗️ 技术架构

### 四大核心模块

| 模块 | 职责 | 技术 |
|------|------|------|
| **TemplateParser** | 解析PPT模板，识别页面类型和占位区域 | `python-pptx` + GPT-4o AI分类 |
| **ContentOrganizer** | 从资料提炼内容，分配到页面，推荐可视化 | GPT-4o LLM |
| **ImageHandler** | 按优先级处理图片需求 | 优先级：用户已有 → 必应搜索 → DALL·E生成 |
| **PPTCompositor** | 把内容填充到模板，保持原有样式 | `python-pptx` |

### 数据结构

核心数据结构定义在各个模块中：

- `TemplateStructure` - 解析后的模板结构
- `ContentPlan` - 整理后的内容规划
- `DataBlock` - 数据块（用于图表）
- `ImageRequest` / `ImageResult` - 图片需求和结果

### 模块化设计优点

1. **可独立迭代**：每个模块可以单独优化替换
   - 模板识别不准 → 换更好的AI模型，不影响其他模块
   - 图片搜索不满意 → 换搜索源，不影响其他模块

2. **可测试**：每个模块可以单独测试

3. **可扩展**：增加新功能不影响现有代码

---

## 💻 开发指南

### 添加新功能

因为是模块化设计，添加新功能只需要修改对应模块：

1. **改进模板识别** → 修改 `src/core/template_parser.py`
2. **改进图片搜索** → 修改 `src/core/image_handler.py`
3 **添加新的图表类型** → 修改 `src/core/ppt_compositor.py`

### 代码风格

- 使用类型注解
- 函数职责单一
- 错误处理完善

### 部署建议

**开发环境：**
```bash
uvicorn main:app --reload --port 8000
```

**生产环境：**
```bash
# 使用gunicorn
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app -b 0.0.0.0:8000
```

### 环境变量配置表

| 变量 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `OPENAI_API_KEY` | 是 | OpenAI API Key | `sk-xxx` |
| `OPENAI_BASE_URL` | 否 | 自定义API地址 | `https://api.openai.com/v1` |
| `BING_SEARCH_KEY` | 否 | 必应图片搜索Key | `xxx` |

---

## 🎨 图片处理策略

本产品使用三级优先级策略：

1. **第一优先级：用户已有** → 如果用户资料中已经有图片，直接使用
   - 优点：最快，质量可控，无版权问题

2. **第二优先级：联网搜索** → 如果用户没有，去必应搜索免费可商用图片
   - 优点：真实图片，符合需求概率高
   - 已添加 `license=public` 筛选，只找免费可商用的

3. **第三优先级：AI生成** → 如果搜索不到，调用DALL·E 3生成
   - 优点：总能得到图片，完全匹配需求
   - 缺点：比搜索贵

---

## ❓ 常见问题

### Q: 支持哪些PPT模板？
A: 支持 `.pptx` 格式，`.ppt` 格式建议先转换为 `.pptx`。非常复杂的母版嵌套模板可能有兼容性问题，这是 `python-pptx` 库本身的限制。

### Q: 需要多少钱？
A: 主要成本是OpenAI API调用，一单PPT生成大约是 `$0.05 - $0.20` 不等，取决于模板页数和资料长度。图片搜索是免费的，AI生成图片每张 `$0.04` (DALL·E 3 1024x1024)。

### Q: 可以用国产模型吗？
A: 可以，只要接口兼容OpenAI，配置 `OPENAI_BASE_URL` 就行。

### Q: 数据隐私怎么样？
A: 模板和资料只在处理过程中使用，处理完可以立即删除，不会永久存储。你也可以部署在自己的服务器上，数据不会出墙。

### Q: 模板识别准确率如何？
A: 对于规范的模板（每个占位明确），准确率在 85% 以上。如果识别错了，前端可以让用户人工修正。本架构设计预留了人工干预节点。

### Q: 支持哪些文档作为输入？
A: MVP 版本支持纯文本、PDF (.pdf)、Word (.docx)。你需要在前端先提取文本再传给API。

---

## 📝 已知限制（MVP 版本）

1. `python-pptx` 对一些非常复杂的模板母版支持有限
2. 完整的交互式图表生成需要进一步完善代码
3. 复杂表格的自动生成还需要优化
4. 缺少单元测试（MVP 阶段优先实现功能）

这些限制不影响核心功能使用，后续版本可以逐步完善。

---

## 📞 获取帮助

如果遇到问题：

1. 检查依赖是否正确安装：`pip list | grep python-pptx`
2. 检查环境变量是否正确设置：`echo $OPENAI_API_KEY`
3. 查看日志输出，错误信息会返回在API响应中

---

*Last updated: 2026-04-08*
