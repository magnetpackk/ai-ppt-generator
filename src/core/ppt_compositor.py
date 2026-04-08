# -*- coding: utf-8 -*-
"""
模块四：PPT Compositor - 内容模板合并生成
将整理好的内容填充到模板对应位置，保持原有样式，输出最终PPT
"""

import io
from io import BytesIO
from typing import List, Dict, Optional, Any

from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE

from .template_parser import TemplateStructure, Placeholder
from .content_organizer import ContentPlan, ContentPage, DataBlock
from .image_handler import ImageResult


class PPTCompositor:
    """PPT合成器"""

    def __init__(self):
        pass

    def compose(
        self,
        template_file: BytesIO,
        template_structure: TemplateStructure,
        content_plan: ContentPlan,
        image_results: List[ImageResult],
    ) -> BytesIO:
        """合成最终PPT"""

        prs = Presentation(template_file)

        # 填充每页内容
        for content_page in content_plan.pages:
            if content_page.slide_index >= len(prs.slides):
                continue

            slide = prs.slides[content_page.slide_index]
            self._fill_slide_content(slide, content_page, template_structure)

        # 插入图片
        self._insert_images(prs, content_plan, image_results, template_structure)

        # 生成数据图表
        self._create_charts(prs, content_plan, template_structure)

        # 输出
        output = BytesIO()
        prs.save(output)
        output.seek(0)
        return output

    def _fill_slide_content(self, slide, content_page: ContentPage, template_structure: TemplateStructure):
        """填充页面文字内容"""

        if not content_page.content or not content_page.content.strip():
            return

        # 找到这页的文字占位
        template_slide = next(
            (s for s in template_structure.slides if s.index == content_page.slide_index),
            None
        )
        if not template_slide:
            return

        text_placeholders = [p for p in template_slide.placeholders if p.type == "text"]

        if len(text_placeholders) == 1:
            # 只有一个文字占位，放全部内容
            ph = text_placeholders[0]
            self._fill_text_placeholder(slide, ph, content_page.content)
        else:
            # 多个占位，拆分内容
            paragraphs = content_page.content.split("\n\n")
            for i, ph in enumerate(text_placeholders):
                if i < len(paragraphs):
                    self._fill_text_placeholder(slide, ph, paragraphs[i])
                else:
                    break

    def _fill_text_placeholder(self, slide, ph: Placeholder, content: str):
        """填充文字到占位符"""

        # 找到对应的形状
        for shape in slide.shapes:
            if shape.shape_id == ph.shape_id:
                if shape.has_text_frame:
                    # 清空原有内容
                    text_frame = shape.text_frame
                    # 保留第一个段落，设置内容
                    text_frame.clear()
                    p = text_frame.paragraphs[0]
                    p.text = content.strip()

                    # 自动调整字号（简单策略）
                    self._auto_fit_font(shape, content)
                break

    def _auto_fit_font(self, shape, content: str):
        """简单自动适配字号"""
        if not shape.has_text_frame:
            return

        text_frame = shape.text_frame
        # 估算合适的字号
        # 占位高度 (Emu -> Point)
        height_pt = shape.height / 12700
        lines = content.count("\n") + 1
        estimated_lines = max(lines, len(content) // 40 + 1)

        # 计算合适字号
        font_size = int(min(height_pt / estimated_lines * 0.8, 24))
        font_size = max(font_size, 10)  # 最小10号

        for paragraph in text_frame.paragraphs:
            for run in paragraph.runs:
                run.font.size = Pt(font_size)

    def _insert_images(
        self,
        prs: Presentation,
        content_plan: ContentPlan,
        image_results: List[ImageResult],
        template_structure: TemplateStructure,
    ):
        """插入图片到对应位置"""

        for img_result in image_results:
            if not img_result.success or not img_result.image_data:
                continue

            # 找到对应的占位
            found_ph = None
            for slide in template_structure.slides:
                for ph in slide.placeholders:
                    if ph.shape_id == img_result.placeholder_id and slide.index == img_result.slide_index:
                        found_ph = ph
                        break
                if found_ph:
                    break

            if not found_ph:
                continue

            if img_result.slide_index >= len(prs.slides):
                continue

            slide = prs.slides[img_result.slide_index]

            # 转换位置（英寸 -> EMU）
            left = Emu(int(found_ph.x * 914400))
            top = Emu(int(found_ph.y * 914400))
            width = Emu(int(found_ph.width * 914400))
            height = Emu(int(found_ph.height * 914400))

            # 插入图片
            try:
                slide.shapes.add_picture(
                    BytesIO(img_result.image_data),
                    left,
                    top,
                    width,
                    height,
                )
            except Exception as e:
                print(f"Failed to insert image: {e}")

    def _create_charts(
        self,
        prs: Presentation,
        content_plan: ContentPlan,
        template_structure: TemplateStructure,
    ):
        """创建图表"""

        for data_block in content_plan.data_blocks:
            if data_block.recommended_type == "table":
                self._create_table(prs, data_block, template_structure)
            else:
                self._create_chart(prs, data_block, template_structure)

    def _create_table(self, prs, data_block: DataBlock, template_structure: TemplateStructure):
        """创建表格"""
        # 简化实现：将数据作为文字填入占位
        # 完整实现需要解析结构化数据创建真实表格
        pass

    def _create_chart(self, prs, data_block: DataBlock, template_structure: TemplateStructure):
        """创建图表"""
        # 完整实现需要根据结构化数据创建对应类型的图表
        # MVP 阶段：数据已经由AI分析推荐好类型，开发阶段进一步完善
        pass

    def _get_chart_type(self, recommended_type: str) -> XL_CHART_TYPE:
        """获取PPT图表类型"""
        mapping = {
            "bar": XL_CHART_TYPE.COLUMN_CLUSTERED,
            "column": XL_CHART_TYPE.COLUMN_CLUSTERED,
            "line": XL_CHART_TYPE.LINE,
            "pie": XL_CHART_TYPE.PIE,
            "scatter": XL_CHART_TYPE.XY_SCATTER,
        }
        return mapping.get(recommended_type, XL_CHART_TYPE.COLUMN_CLUSTERED)
