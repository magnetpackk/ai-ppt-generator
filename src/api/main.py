# -*- coding: utf-8 -*-
"""
FastAPI 服务入口
AI PPT Generator API
"""

import os
import io
from io import BytesIO
from typing import Optional, List
import tempfile

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.template_parser import TemplateParser, TemplateStructure
from src.core.content_organizer import ContentOrganizer, ContentPlan
from src.core.image_handler import ImageHandler
from src.core.ppt_compositor import PPTCompositor


app = FastAPI(
    title="AI PPT Generator",
    description="基于模板的AI PPT生成器，双输入：模板+资料，自动填充内容",
    version="0.1.0",
)


# ========== 配置 ==========
class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", None)
    BING_SEARCH_KEY = os.getenv("BING_SEARCH_KEY", None)


# ========== 请求模型 ==========
class ParseTemplateResponse(BaseModel):
    success: bool
    slide_count: int = Field(0, description="模板页数")
    structure: Optional[dict] = Field(None, description="解析后的模板结构")
    error: Optional[str] = Field(None, description="错误信息")


class OrganizeContentRequest(BaseModel):
    source_text: str = Field(..., description="用户资料文本")
    template_structure: dict = Field(..., description="解析后的模板结构")


class OrganizeContentResponse(BaseModel):
    success: bool
    content_plan: Optional[dict] = None
    error: Optional[str] = None


class GeneratePPTRequest(BaseModel):
    template_file: bytes = Field(..., description="模板文件二进制")
    content_plan: dict = Field(..., description="内容规划")
    template_structure: dict = Field(..., description="模板结构")


# ========== API 路由 ==========

@app.get("/")
def root():
    return {
        "name": "AI PPT Generator",
        "version": "0.1.0",
        "status": "ok",
    }


@app.post("/api/parse-template", response_model=ParseTemplateResponse)
async def parse_template(template: UploadFile = File(...)):
    """解析PPT模板，返回结构信息"""

    if not template.filename.endswith(('.pptx', '.ppt')):
        raise HTTPException(status_code=400, detail="Only .pptx files are supported")

    try:
        content = await template.read()
        template_file = BytesIO(content)

        parser = TemplateParser(
            openai_api_key=Config.OPENAI_API_KEY,
            openai_base_url=Config.OPENAI_BASE_URL,
        )

        structure = parser.parse(template_file)

        # 转换为dict返回
        result = {
            "slide_count": structure.slide_count,
            "slides": [
                {
                    "index": s.index,
                    "page_type": s.page_type,
                    "placeholders": [
                        {
                            "shape_id": p.shape_id,
                            "type": p.type,
                            "x": p.x, "y": p.y, "width": p.width, "height": p.height,
                        }
                        for p in s.placeholders
                    ],
                }
                for s in structure.slides
            ],
            "theme": {
                "background_color": structure.theme.background_color,
                "font_family": structure.theme.font_family,
                "color_scheme": structure.theme.color_scheme,
            }
        }

        return ParseTemplateResponse(
            success=True,
            slide_count=structure.slide_count,
            structure=result,
        )

    except Exception as e:
        return ParseTemplateResponse(
            success=False,
            error=str(e),
        )


@app.post("/api/organize-content", response_model=OrganizeContentResponse)
def organize_content(req: OrganizeContentRequest):
    """整理用户资料，生成内容规划"""

    try:
        # 这里简化处理，实际需要先反序列化TemplateStructure
        organizer = ContentOrganizer(
            openai_api_key=Config.OPENAI_API_KEY,
            openai_base_url=Config.OPENAI_BASE_URL,
        )

        # 简化实现，实际需要完整反序列化
        # 这里直接调用AI生成内容规划
        # 前端保存结构，传给后端

        # TODO: 反序列化TemplateStructure
        # 临时：直接返回AI处理结果
        return OrganizeContentResponse(
            success=True,
            content_plan=None,  # 实际填充结果
            error=None,
        )

    except Exception as e:
        return OrganizeContentResponse(
            success=False,
            error=str(e),
        )


@app.post("/api/generate-ppt")
async def generate_ppt(
    template: UploadFile = File(...),
):
    """生成最终PPT"""
    try:
        template_content = await template.read()
        template_file = BytesIO(template_content)

        # 解析模板
        parser = TemplateParser(
            openai_api_key=Config.OPENAI_API_KEY,
            openai_base_url=Config.OPENAI_BASE_URL,
        )
        template_structure = parser.parse(template_file)

        # TODO: 获取内容规划，处理图片，合成
        # 完整流程需要前端分步处理

        compositor = PPTCompositor()
        # 合成...

        # 输出
        output = BytesIO()
        # compositor.compose(...) -> output
        # 返回 FileResponse

        raise NotImplementedError("Full generation not implemented in MVP")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
