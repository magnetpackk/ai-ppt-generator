# -*- coding: utf-8 -*-
"""
AI PPT Generator - Core Module
"""

from .template_parser import TemplateParser
from .content_organizer import ContentOrganizer
from .image_handler import ImageHandler
from .ppt_compositor import PPTCompositor

__version__ = "0.1.0"
__all__ = [
    "TemplateParser",
    "ContentOrganizer",
    "ImageHandler",
    "PPTCompositor",
]
