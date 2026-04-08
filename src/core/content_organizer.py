# -*- coding: utf-8 -*-
"""
模块二：Content Organizer - 知识库内容整理
从用户资料提炼PPT大纲，推荐数据可视化，生成图片需求
"""

import re
import openai
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

from .template_parser import TemplateStructure, SlideInfo


@dataclass
class ContentPage:
    """单页内容"""
    template_page_type: str
    content: str


@dataclass
class DataBlock:
    """数据块"""
    template_page_type: str
    placeholder_type: str
    raw_data: str
    structured_data: Any
    recommended_type: str  # table | bar | line | pie | scatter
    title: str


@dataclass
class ImageRequest:
    """图片需求"""
    template_page_type: str
    placeholder_type: str
    keywords: List[str]
    priority: str  # user-provided | search | generate
    description: str
    width: Optional[int] = None
    height: Optional[int] = None


@dataclass
class ContentPlan:
    """完整内容规划"""
    pages: List[ContentPage]
    data_blocks: List[DataBlock]
    image_requests: List[ImageRequest]


class ContentOrganizer:
    """内容整理器"""

    def __init__(self, openai_api_key: str, openai_base_url: Optional[str] = None, model: str = "gpt-4o"):
        self.openai_api_key = openai_api_key
        self.openai_base_url = openai_base_url
        self.model = model
        self.client = openai.OpenAI(
            api_key=openai_api_key,
            base_url=openai_base_url,
        )

    def organize(
        self,
        source_text: str,
        template_structure: TemplateStructure,
    ) -> ContentPlan:
        """整理内容，生成PPT大纲规划"""

        # 构建prompt给AI
        prompt = self._build_organize_prompt(source_text, template_structure)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是PPT内容整理专家。请根据用户提供的资料和PPT模板库，"
                        "把内容整理规划成完整PPT，输出JSON格式。"
                        "模板库提供了不同类型的页面模板，你根据内容决定需要多少页，选择对应类型的模板。"
                    )
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        result_text = response.choices[0].message.content.strip()

        # 解析AI输出
        import json
        try:
            data = json.loads(result_text)
            return self._parse_ai_output(data)
        except Exception as e:
            raise ValueError(f"Failed to parse AI output: {e}")

    def _build_organize_prompt(self, source_text: str, template_structure: TemplateStructure) -> str:
        """构建整理prompt"""

        # 统计模板库中每种类型有多少页
        template_types: Dict[str, int] = {}
        template_details = ""
        for idx, slide in enumerate(template_structure.slides):
            slide_type = slide.page_type
            template_types[slide_type] = template_types.get(slide_type, 0) + 1
            placeholders = [f"  - {p.type}占位 (estimated text length={p.expected_text_length})" for p in slide.placeholders]
            template_details += f"- 模板页 #{idx} 类型={slide.page_type}:\n" + "\n".join(placeholders) + "\n\n"

        return f"""请帮我整理这份PPT内容：

## 原始资料
{source_text[:8000]}  # 限制长度

## 模板库
模板提供了不同类型的页面，你可以根据内容需要选择使用：
{template_details}

## 要求
**请根据资料内容，决定PPT总共需要多少页，然后从模板库中选择对应类型的页面来容纳内容。**

请按以下JSON格式输出：

{{
  "pages": [
    {{
      "template_page_type": "选择使用的页面类型: cover/toc/title/content/section/blank",
      "content": "整理后适合放在这页的文字内容，如果是目录需要每一项占一行"
    }}
  ],
  "data_blocks": [
    {{
      "template_page_type": "选择使用的页面类型",
      "placeholder_type": "占位类型 text/chart/table",
      "raw_data": "原始数据文本",
      "recommended_type": "推荐可视化类型 table|bar|line|pie",
      "title": "数据标题"
    }}
  ],
  "image_requests": [
    {{
      "template_page_type": "选择使用的页面类型",
      "placeholder_type": "image",
      "keywords": ["关键词1", "关键词2"],
      "priority": "search" 或 "generate",
      "description": "图片描述"
    }}
  ]
}}

核心规则：
1. **根据资料内容自由决定页数**，不要受模板原有页数限制。模板只是给你提供不同类型的页面样式，你决定需要多少页就生成多少页。
2. **合理分配内容到占位符**：如果一个页面模板有多个文本占位符（比如目录页每个目录项一个占位），一定要把内容拆分到对应的占位符，不要把所有内容都挤到第一个占位符。
3. **保持排版美观**：目录应该每个目录项单独放一个占位，如果内容超过占位符数量，保持纵向分行排列，左对齐。
4. 识别出表格数据和图表数据，给出推荐可视化类型
5. 需要图片的位置生成图片需求，有明确关键词就search，需要示意图就generate
6. 文字要简洁适合PPT，不要大段文字
"""

    def _parse_ai_output(self, data: dict) -> ContentPlan:
        """解析AI输出"""

        pages: List[ContentPage] = []
        for p in data.get("pages", []):
            pages.append(ContentPage(
                template_page_type=p.get("template_page_type", "content"),
                content=p.get("content", ""),
            ))

        data_blocks: List[DataBlock] = []
        for db in data.get("data_blocks", []):
            data_blocks.append(DataBlock(
                template_page_type=db.get("template_page_type", "content"),
                placeholder_type=db.get("placeholder_type", "text"),
                raw_data=db.get("raw_data", ""),
                structured_data=db.get("structured_data", None),
                recommended_type=db.get("recommended_type", "table"),
                title=db.get("title", ""),
            ))

        image_requests: List[ImageRequest] = []
        for ir in data.get("image_requests", []):
            image_requests.append(ImageRequest(
                template_page_type=ir.get("template_page_type", "content"),
                placeholder_type=ir.get("placeholder_type", "image"),
                keywords=ir.get("keywords", []),
                priority=ir.get("priority", "search"),
                description=ir.get("description", ""),
            ))

        return ContentPlan(
            pages=pages,
            data_blocks=data_blocks,
            image_requests=image_requests,
        )

    def _extract_data_blocks(self, text: str) -> List[Dict]:
        """从文本中提取数据块（预处理，AI会进一步处理）"""
        # 简单正则匹配表格类数据
        # 实际由AI处理更灵活
        return []
