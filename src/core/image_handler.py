# -*- coding: utf-8 -*-
"""
模块三：ImageHandler - 图片处理
按优先级处理图片需求：用户已有 → 联网搜索 → AI生成
"""

import os
import requests
import openai
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from .template_parser import Placeholder


@dataclass
class ImageRequest:
    """图片需求"""
    slide_index: int
    placeholder_id: int
    keywords: List[str]
    priority: str  # user-provided | search | generate
    description: str
    width: Optional[int] = None
    height: Optional[int] = None


@dataclass
class ImageResult:
    """图片处理结果"""
    slide_index: int
    placeholder_id: int
    success: bool
    image_url: Optional[str] = None
    image_data: Optional[bytes] = None
    source: Optional[str] = None  # user | search | generate
    error: Optional[str] = None


class ImageHandler:
    """图片处理器"""

    def __init__(
        self,
        bing_search_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        openai_base_url: Optional[str] = None,
    ):
        self.bing_search_key = bing_search_key
        self.openai_api_key = openai_api_key
        if openai_api_key:
            self.openai_client = openai.OpenAI(
                api_key=openai_api_key,
                base_url=openai_base_url,
            )
        else:
            self.openai_client = None

    def process_all(self, image_requests: List[ImageRequest]) -> List[ImageResult]:
        """处理所有图片需求"""
        results = []
        for req in image_requests:
            result = self.process_one(req)
            results.append(result)
        return results

    def process_one(self, req: ImageRequest) -> ImageResult:
        """按照优先级处理单个图片需求"""

        # 优先级 1: 用户已有
        if req.priority == "user-provided":
            # 用户已经提供图片，直接返回
            # 这里应该从用户上传资料中提取，上层处理
            return ImageResult(
                slide_index=req.slide_index,
                placeholder_id=req.placeholder_id,
                success=True,
                source="user",
            )

        # 优先级 2: 联网搜索
        if req.priority == "search" and self.bing_search_key:
            search_result = self._search_image(req)
            if search_result.success:
                return search_result

        # 优先级 3: AI 生成
        if req.priority == "generate" and self.openai_client:
            generate_result = self._generate_image(req)
            if generate_result.success:
                return generate_result

        # 所有都失败
        return ImageResult(
            slide_index=req.slide_index,
            placeholder_id=req.placeholder_id,
            success=False,
            error="All methods failed",
        )

    def _search_image(self, req: ImageRequest) -> ImageResult:
        """必应图片搜索"""
        if not self.bing_search_key:
            return ImageResult(
                slide_index=req.slide_index,
                placeholder_id=req.placeholder_id,
                success=False,
                error="Bing search key not configured",
            )

        query = " ".join(req.keywords)
        # 只搜索免费可商用图片
        url = "https://api.bing.microsoft.com/v7.0/images/search"
        headers = {"Ocp-Apim-Subscription-Key": self.bing_search_key}
        params = {
            "q": query,
            "count": 1,
            "license": "public",  # 免费可商用
            "imageType": "photo",
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "value" in data and len(data["value"]) > 0:
                first_result = data["value"][0]
                image_url = first_result["contentUrl"]

                # 下载图片
                img_response = requests.get(image_url, timeout=10)
                if img_response.status_code == 200:
                    return ImageResult(
                        slide_index=req.slide_index,
                        placeholder_id=req.placeholder_id,
                        success=True,
                        image_url=image_url,
                        image_data=img_response.content,
                        source="search",
                    )

            return ImageResult(
                slide_index=req.slide_index,
                placeholder_id=req.placeholder_id,
                success=False,
                error="No search results",
            )

        except Exception as e:
            return ImageResult(
                slide_index=req.slide_index,
                placeholder_id=req.placeholder_id,
                success=False,
                error=f"Search failed: {str(e)}",
            )

    def _generate_image(self, req: ImageRequest) -> ImageResult:
        """DALL·E 生成图片"""
        if not self.openai_client:
            return ImageResult(
                slide_index=req.slide_index,
                placeholder_id=req.placeholder_id,
                success=False,
                error="OpenAI not configured",
            )

        prompt = req.description
        if req.keywords:
            prompt += ", keywords: " + ", ".join(req.keywords)

        # 添加风格提示
        prompt += ", business presentation style, high quality"

        size = "1024x1024"
        if req.width and req.height:
            aspect = req.width / req.height
            if aspect > 1.5:
                size = "1792x1024"
            elif aspect < 0.67:
                size = "1024x1792"

        try:
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                n=1,
            )

            if response.data and len(response.data) > 0:
                image_url = response.data[0].url
                # 下载图片
                img_response =requests.get(image_url, timeout=30)
                if img_response.status_code == 200:
                    return ImageResult(
                        slide_index=req.slide_index,
                        placeholder_id=req.placeholder_id,
                        success=True,
                        image_url=image_url,
                        image_data=img_response.content,
                        source="generate",
                    )

            return ImageResult(
                slide_index=req.slide_index,
                placeholder_id=req.placeholder_id,
                success=False,
                error="No generation result",
            )

        except Exception as e:
            return ImageResult(
                slide_index=req.slide_index,
                placeholder_id=req.placeholder_id,
                success=False,
                error=f"Generation failed: {str(e)}",
            )
