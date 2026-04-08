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
    slide_index: int
    page_type: str
    content: str


@dataclass
class DataBlock:
    """数据块"""
    slide_index: int
    placeholder_id: int
    raw_data: str
    structured_data: Any
    recommended_type: str  # table | bar | line | pie | scatter
    title: str


@dataclass
class ImageRequest:
    """图片需求"""
    slide_index: int
    placeholder_id: int
    keywords: List[str]
    priority: str  # user-provided | search | generate
    description: str


@dataclass
class ContentPlan:
    """完整内容规划"""
    pages: List[ContentPage]
    data_blocks: List[DataBlock]
    image_requests: List[ImageRequest]


class ContentOrganizer:
    """内容整理器"""

    def __init__(self, openai_api_key: str, openai_base_url: Optional[str] = None):
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
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是PPT内容整理专家。请根据用户提供的资料和PPT模板结构，"
                        "把内容整理分配到对应页面，输出JSON格式。"
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
            return self._parse_ai_output(data, template_structure)
        except Exception as e:
            raise ValueError(f"Failed to parse AI output: {e}")

    def _build_organize_prompt(self, source_text: str, template_structure: TemplateStructure) -> str:
        """构建整理prompt"""

        template_info = "模板结构:\n"
        for slide in template_structure.slides:
            placeholders = [f"  - {p.type}占位 (id={p.shape_id})" for p in slide.placeholders]
            template_info += f"页面 {slide.index} 类型={slide.page_type}:\n" + "\n".join(placeholders) + "\n\n"

        return f"""请帮我整理这份PPT内容：

## 原始资料
{source_text[:8000]}  # 限制长度

## 模板结构
{template_info}

## 要求
请按以下JSON格式输出：

{{
  "pages": [
    {{
      "slide_index": 页面索引,
      "page_type": "页面类型",
      "content": "整理后适合放在这页的文字内容"
    }}
  ],
  "data_blocks": [
    {{
      "slide_index": 页面索引,
      "placeholder_id": 占位id,
      "raw_data": "原始数据文本",
      "recommended_type": "推荐可视化类型 table|bar|line|pie",
      "title": "数据标题"
    }}
  ],
  "image_requests": [
    {{
      "slide_index": 页面索引,
      "placeholder_id": 占位id,
      "keywords": ["关键词1", "关键词2"],
      "priority": "search" 或 "generate",
      "description": "图片描述"
    }}
  ]
}}

规则：
1. 内容必须匹配模板页面数量和类型，封面放标题，目录页放目录
2. 识别出表格数据和图表数据，给出推荐可视化类型
3. 需要图片的位置生成图片需求，有明确关键词就search，需要示意图就generate
4. 文字要简洁适合PPT，不要大段文字
"""

    def _parse_ai_output(self, data: dict, template_structure: TemplateStructure) -> ContentPlan:
        """解析AI输出"""

        pages: List[ContentPage] = []
        for p in data.get("pages", []):
            pages.append(ContentPage(
                slide_index=int(p.get("slide_index", 0)),
                page_type=p.get("page_type", "content"),
                content=p.get("content", ""),
            ))

        data_blocks: List[DataBlock] = []
        for db in data.get("data_blocks", []):
            data_blocks.append(DataBlock(
                slide_index=int(db.get("slide_index", 0)),
                placeholder_id=int(db.get("placeholder_id", 0)),
                raw_data=db.get("raw_data", ""),
                structured_data=db.get("structured_data", None),
                recommended_type=db.get("recommended_type", "table"),
                title=db.get("title", ""),
            ))

        image_requests: List[ImageRequest] = []
        for ir in data.get("image_requests", []):
            image_requests.append(ImageRequest(
                slide_index=int(ir.get("slide_index", 0)),
                placeholder_id=int(ir.get("placeholder_id", 0)),
                keywords=ir.get("keywords", []),
                priority=ir.get("priority", "search"),
                description=ir.get("description", ""),
            ))

        # 对齐模板，确保每个页面都有内容
        result_pages = []
        template_slide_indexes = [s.index for s in template_structure.slides]
        # 先加AI生成的
        for page in pages:
            if page.slide_index in template_slide_indexes:
                result_pages.append(page)
        # 补全缺失的
        for slide in template_structure.slides:
            if not any(p.slide_index == slide.index for p in result_pages):
                result_pages.append(ContentPage(
                    slide_index=slide.index,
                    page_type=slide.page_type,
                    content="",
                ))

        return ContentPlan(
            pages=result_pages,
            data_blocks=data_blocks,
            image_requests=image_requests,
        )

    def _extract_data_blocks(self, text: str) -> List[Dict]:
        """从文本中提取数据块（预处理，AI会进一步处理）"""
        # 简单正则匹配表格类数据
        # 实际由AI处理更灵活
        return []
