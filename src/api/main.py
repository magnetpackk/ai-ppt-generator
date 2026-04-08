# -*- coding: utf-8 -*-
"""
FastAPI 服务入口
AI PPT Generator - 完整Web界面端到端
"""

import os
import io
import json
from io import BytesIO
from typing import Optional, Dict
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.template_parser import TemplateParser, TemplateStructure, SlideInfo
from src.core.content_organizer import ContentOrganizer, ContentPlan
from src.core.image_handler import ImageHandler
from src.core.ppt_compositor import PPTCompositor

# 文档解析
from PyPDF2 import PdfReader
from docx import Document as DocxDocument


app = FastAPI(
    title="AI PPT Generator",
    description="基于模板的AI PPT生成器，双输入：模板+资料，自动填充内容",
    version="1.1.0",
)


# ========== 存储用户配置（内存存储，重启后清空） ==========
user_config = {
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    "openai_base_url": os.getenv("OPENAI_BASE_URL", ""),
    "openai_model": "gpt-4o",
    "image_search_provider": "none",
    "bing_search_key": os.getenv("BING_SEARCH_KEY", ""),
    "tavily_api_key": os.getenv("TAVILY_API_KEY", ""),
    "bocha_api_key": os.getenv("BOCHA_API_KEY", ""),
}


# ========== HTML 界面 ==========
INDEX_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI PPT 生成器</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }
        .tabs {
            display: flex;
            margin-bottom: 20px;
            border-bottom: 2px solid #ddd;
        }
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            border: none;
            background: none;
            font-size: 16px;
            color: #666;
            margin-bottom: -2px;
        }
        .tab.active {
            color: #007bff;
            border-bottom: 2px solid #007bff;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .card {
            background: white;
            border-radius: 8px;
            padding: 25px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #333;
        }
        input[type="text"], input[type="password"], select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        input[type="file"] {
            padding: 10px 0;
        }
        .file-upload {
            border: 2px dashed #ddd;
            border-radius: 8px;
            padding: 30px;
            text-align: center;
            cursor: pointer;
            transition: border-color 0.3s;
        }
        .file-upload:hover {
            border-color: #007bff;
        }
        .file-upload input {
            display: none;
        }
        .file-info {
            margin-top: 10px;
            color: #666;
            font-size: 14px;
        }
        .btn {
            display: inline-block;
            padding: 12px 30px;
            font-size: 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        .btn-primary {
            background: #007bff;
            color: white;
        }
        .btn-primary:hover {
            background: #0056b3;
        }
        .btn-primary:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .btn-success {
            background: #28a745;
            color: white;
        }
        .btn-success:hover {
            background: #218838;
        }
        .center {
            text-align: center;
        }
        .progress {
            margin: 20px 0;
            display: none;
        }
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #eee;
            border-radius: 4px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: #007bff;
            width: 0%;
            transition: width 0.3s;
        }
        .progress-text {
            margin-top: 8px;
            text-align: center;
            color: #666;
            font-size: 14px;
        }
        .result {
            margin-top: 20px;
            display: none;
        }
        .error {
            margin-top: 20px;
            padding: 15px;
            background: #f8d7da;
            color: #721c24;
            border-radius: 4px;
            display: none;
        }
        .help-text {
            font-size: 13px;
            color: #888;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <h1>🤖 AI PPT 生成器</h1>
    <p class="subtitle">基于已有模板，自动填充内容生成PPT</p>

    <div class="tabs">
        <button class="tab active" onclick="switchTab('config')">⚙️ 配置</button>
        <button class="tab" onclick="switchTab('generate')">📄 生成</button>
    </div>

    <!-- 配置页 -->
    <div id="config-tab" class="tab-content active">
        <div class="card">
            <div class="form-group">
                <label for="openai_api_key">OpenAI API Key</label>
                <input type="password" id="openai_api_key" placeholder="sk-..." value="">
            </div>
            <div class="form-group">
                <label for="openai_base_url">OpenAI Base URL (可选)</label>
                <input type="text" id="openai_base_url" placeholder="https://api.openai.com/v1" value="">
                <p class="help-text">使用中转服务时填写，留空使用默认</p>
            </div>
            <div class="form-group">
                <label for="openai_model">AI 模型</label>
                <select id="openai_model">
                    <option value="gpt-4o" selected>gpt-4o (推荐)</option>
                    <option value="gpt-4-turbo">gpt-4-turbo</option>
                    <option value="gpt-4">gpt-4</option>
                    <option value="gpt-3.5-turbo">gpt-3.5-turbo</option>
                </select>
            </div>
            <div class="form-group">
                <label for="image_search_provider">图片搜索服务 (可选)</label>
                <select id="image_search_provider">
                    <option value="none" selected>不搜索图片</option>
                    <option value="bing">Bing Image Search</option>
                    <option value="tavily">Tavily AI Search</option>
                    <option value="bocha">博查 AI Search</option>
                </select>
                <p class="help-text">选择图片搜索服务，搜索到的图片会自动插入PPT对应位置</p>
            </div>
            <div class="form-group" id="bing_key_group">
                <label for="bing_search_key">Bing Search API Key</label>
                <input type="password" id="bing_search_key" placeholder="" value="">
            </div>
            <div class="form-group" id="tavily_key_group">
                <label for="tavily_api_key">Tavily API Key</label>
                <input type="password" id="tavily_api_key" placeholder="" value="">
            </div>
            <div class="form-group" id="bocha_key_group">
                <label for="bocha_api_key">博查 API Key</label>
                <input type="password" id="bocha_api_key" placeholder="" value="">
                <p class="help-text">API endpoint: https://api.bocha.cn/v1/web-search</p>
            </div>
            <div class="center">
                <button class="btn btn-primary" onclick="saveConfig()">保存配置</button>
            </div>
            <div id="config-message" style="margin-top: 15px; text-align: center; display: none;"></div>
        </div>
    </div>

    <!-- 生成页 -->
    <div id="generate-tab" class="tab-content">
        <div class="card">
            <div class="form-group">
                <label>1. 上传 PPT 模板</label>
                <div class="file-upload" onclick="document.getElementById('template_file').click()">
                    <input type="file" id="template_file" accept=".pptx" onchange="onFileSelect('template', this)">
                    <p>点击上传 .pptx 模板文件</p>
                </div>
                <div id="template_info" class="file-info"></div>
            </div>

            <div class="form-group">
                <label>2. 上传资料文件</label>
                <div class="file-upload" onclick="document.getElementById('source_file').click()">
                    <input type="file" id="source_file" accept=".txt,.pdf,.docx,.doc" onchange="onFileSelect('source', this)">
                    <p>点击上传资料（支持 .txt .pdf .docx）</p>
                </div>
                <div id="source_info" class="file-info"></div>
            </div>

            <div class="center">
                <button class="btn btn-primary" id="generate_btn" onclick="generatePPT()" disabled>
                    🚀 开始生成 PPT
                </button>
            </div>

            <div id="progress" class="progress">
                <div class="progress-bar">
                    <div id="progress_fill" class="progress-fill"></div>
                </div>
                <div id="progress_text" class="progress-text">正在处理...</div>
            </div>

            <div id="error_box" class="error"></div>

            <div id="result" class="result">
                <h3 style="color: #28a745; margin-bottom: 15px; text-align: center;">✅ 生成完成！</h3>
                <div class="center">
                    <a id="download_link" class="btn btn-success" download>📥 下载 PPT 文件</a>
                </div>
            </div>
        </div>
    </div>

<script>
    // 显示隐藏对应的API Key输入框
    function updateKeyVisibility() {
        const provider = document.getElementById('image_search_provider').value;
        document.getElementById('bing_key_group').style.display = provider === 'bing' ? 'block' : 'none';
        document.getElementById('tavily_key_group').style.display = provider === 'tavily' ? 'block' : 'none';
        document.getElementById('bocha_key_group').style.display = provider === 'bocha' ? 'block' : 'none';
    }

    document.addEventListener('DOMContentLoaded', function() {
        if (document.getElementById('image_search_provider')) {
            document.getElementById('image_search_provider').addEventListener('change', updateKeyVisibility);
            updateKeyVisibility();
        }
    });

    // 初始化
    function switchTab(tabName) {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
        event.target.classList.add('active');
        document.getElementById(tabName + '-tab').classList.add('active');
    }

    function onFileSelect(type, input) {
        const file = input.files[0];
        if (file) {
            document.getElementById(type + '_info').textContent = `已选择: ${file.name} (${formatFileSize(file.size)})`;
        }
        checkGenerateButton();
    }

    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    function checkGenerateButton() {
        const template = document.getElementById('template_file').files[0];
        const source = document.getElementById('source_file').files[0];
        document.getElementById('generate_btn').disabled = !(template && source);
    }

    function saveConfig() {
        const data = {
            openai_api_key: document.getElementById('openai_api_key').value,
            openai_base_url: document.getElementById('openai_base_url').value,
            openai_model: document.getElementById('openai_model').value,
            image_search_provider: document.getElementById('image_search_provider').value,
            bing_search_key: document.getElementById('bing_search_key').value,
            tavily_api_key: document.getElementById('tavily_api_key').value,
            bocha_api_key: document.getElementById('bocha_api_key').value,
        };
        fetch('/api/save-config', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data),
        })
        .then(res => res.json())
        .then(data => {
            const msgBox = document.getElementById('config-message');
            msgBox.style.display = 'block';
            if (data.success) {
                msgBox.innerHTML = '<span style="color: green;">✅ 配置保存成功！</span>';
            } else {
                msgBox.innerHTML = '<span style="color: red;">❌ 保存失败: ' + data.error + '</span>';
            }
            setTimeout(() => msgBox.style.display = 'none', 3000);
        });
    }

    function generatePPT() {
        const templateFile = document.getElementById('template_file').files[0];
        const sourceFile = document.getElementById('source_file').files[0];

        const formData = new FormData();
        formData.append('template', templateFile);
        formData.append('source', sourceFile);

        document.getElementById('progress').style.display = 'block';
        document.getElementById('error_box').style.display = 'none';
        document.getElementById('result').style.display = 'none';
        document.getElementById('generate_btn').disabled = true;

        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 90) progress = 90;
            document.getElementById('progress_fill').style.width = progress + '%';
        }, 500);

        fetch('/api/generate-full', {
            method: 'POST',
            body: formData,
        })
        .then(async response => {
            clearInterval(progressInterval);
            document.getElementById('progress_fill').style.width = '100%%%
            document.getElementById('progress_fill').style.width = '100%';
            if (!response.ok) {
                const err = await response.text();
                throw new Error(err);
            }
            return response.blob();
        })
        .then(blob => {
            document.getElementById('progress').style.display = 'none';
            document.getElementById('result').style.display = 'block';
            const url = window.URL.createObjectURL(blob);
            const downloadLink = document.getElementById('download_link');
            downloadLink.href = url;
            downloadLink.download = templateFile.name.replace('.pptx', '_generated.pptx');
            document.getElementById('generate_btn').disabled = false;
        })
        .catch(err => {
            clearInterval(progressInterval);
            document.getElementById('progress').style.display = 'none';
            document.getElementById('error_box').style.display = 'block';
            document.getElementById('error_box').textContent = '❌ 生成失败: ' + err.message;
            document.getElementById('generate_btn').disabled = false;
        });
    }

    // 加载保存的配置
    fetch('/api/get-config')
        .then(res => res.json())
        .then(data => {
            if (data.openai_api_key) {
                document.getElementById('openai_api_key').value = data.openai_api_key;
            }
            if (data.openai_base_url) {
                document.getElementById('openai_base_url').value = data.openai_base_url;
            }
            if (data.openai_model) {
                document.getElementById('openai_model').value = data.openai_model;
            }
            if (data.image_search_provider) {
                document.getElementById('image_search_provider').value = data.image_search_provider;
            }
            if (data.bing_search_key) {
                document.getElementById('bing_search_key').value = data.bing_search_key;
            }
            if (data.tavily_api_key) {
                document.getElementById('tavily_api_key').value = data.tavily_api_key;
            }
            if (data.bocha_api_key) {
                document.getElementById('bocha_api_key').value = data.bocha_api_key;
            }
            updateKeyVisibility();
        });
</script>
</body>
</html>
"""


# ========== 辅助函数：解析不同文档 ==========
def extract_text_from_file(filename: str, content: bytes) -> str:
    """从不同文件类型提取文本"""
    ext = filename.lower().split('.')[-1]
    if ext == 'txt':
        return content.decode('utf-8', errors='replace')
    elif ext == 'pdf':
        pdf_reader = PdfReader(BytesIO(content))
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"
        return text
    elif ext in ['docx', 'doc']:
        doc = DocxDocument(BytesIO(content))
        text = ""
        for para in doc.paragraphs:
            if para.text:
                text += para.text + "\n"
        return text
    else:
        return content.decode('utf-8', errors='replace')


# ========== API 路由 ==========

@app.get("/", response_class=HTMLResponse)
async def index():
    """主页返回HTML界面"""
    html = INDEX_HTML
    # JavaScript会从API加载配置，这里不需要插值
    return HTMLResponse(content=html)


@app.get("/api/get-config")
def get_config():
    """获取当前配置"""
    return {
        "openai_api_key": user_config.get('openai_api_key', ''),
        "openai_base_url": user_config.get('openai_base_url', ''),
        "openai_model": user_config.get('openai_model', 'gpt-4o'),
        "image_search_provider": user_config.get('image_search_provider', 'none'),
        "bing_search_key": user_config.get('bing_search_key', ''),
        "tavily_api_key": user_config.get('tavily_api_key', ''),
        "bocha_api_key": user_config.get('bocha_api_key', ''),
    }


class SaveConfigRequest(BaseModel):
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    openai_model: Optional[str] = None
    image_search_provider: Optional[str] = None
    bing_search_key: Optional[str] = None
    tavily_api_key: Optional[str] = None
    bocha_api_key: Optional[str] = None


@app.post("/api/save-config")
def save_config(req: SaveConfigRequest):
    """保存用户配置"""
    try:
        if req.openai_api_key is not None:
            user_config['openai_api_key'] = req.openai_api_key
        if req.openai_base_url is not None:
            user_config['openai_base_url'] = req.openai_base_url
        if req.openai_model is not None:
            user_config['openai_model'] = req.openai_model
        if req.image_search_provider is not None:
            user_config['image_search_provider'] = req.image_search_provider
        if req.bing_search_key is not None:
            user_config['bing_search_key'] = req.bing_search_key
        if req.tavily_api_key is not None:
            user_config['tavily_api_key'] = req.tavily_api_key
        if req.bocha_api_key is not None:
            user_config['bocha_api_key'] = req.bocha_api_key
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/generate-full")
async def generate_full(
    template: UploadFile = File(...),
    source: UploadFile = File(...),
):
    """端到端完整生成PPT"""

    # 检查配置
    if not user_config['openai_api_key']:
        raise HTTPException(status_code=400, detail="请先在配置页填写OpenAI API Key")

    try:
        # 1. 读取模板
        template_content = await template.read()
        if not template.filename.endswith('.pptx'):
            raise HTTPException(status_code=400, detail="模板必须是 .pptx 文件")

        # 2. 读取并提取资料文本
        source_content = await source.read()
        source_text = extract_text_from_file(source.filename, source_content)

        if len(source_text.strip()) == 0:
            raise HTTPException(status_code=400, detail="未能从资料文件提取到文本")

        base_url = user_config['openai_base_url'] if user_config['openai_base_url'] else None

        # 3. 解析模板结构
        template_io = BytesIO(template_content)
        parser = TemplateParser(
            openai_api_key=user_config['openai_api_key'],
            openai_base_url=base_url,
            model=user_config['openai_model'],
        )

        template_structure = parser.parse(template_io)

        # 4. 整理内容
        organizer = ContentOrganizer(
            openai_api_key=user_config['openai_api_key'],
            openai_base_url=base_url,
            model=user_config['openai_model'],
        )

        content_plan = organizer.organize(source_text, template_structure)

        # 5. 处理图片需求 - 根据选择的provider
        provider = user_config.get('image_search_provider', 'none')
        image_handler = ImageHandler(
            image_provider=provider,
            bing_search_key=user_config.get('bing_search_key'),
            tavily_api_key=user_config.get('tavily_api_key'),
            bocha_api_key=user_config.get('bocha_api_key'),
            openai_api_key=user_config['openai_api_key'] if content_plan.image_requests else None,
            openai_base_url=base_url,
        )
        image_results = []
        if provider != 'none' and content_plan.image_requests:
            image_results = image_handler.process_all(content_plan.image_requests)

        # 6. 合成最终PPT
        compositor = PPTCompositor()
        output_io = compositor.compose(
            BytesIO(template_content),
            template_structure,
            content_plan,
            image_results,
        )
        output_io.seek(0)

        # 7. 返回文件下载
        output_bytes = output_io.getvalue()

        # 保存到临时文件返回
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(suffix='.pptx', delete=False)
        temp_file.write(output_bytes)
        temp_file.close()

        download_name = template.filename.replace('.pptx', '_generated.pptx') if template.filename else 'generated.pptx'

        return FileResponse(
            temp_file.name,
            media_type='application/vnd.openxmlformats-officedocument.presentationml.presentation',
            filename=download_name,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
