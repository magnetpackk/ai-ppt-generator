# 测试说明

## 环境准备

```bash
pip install -r requirements.txt
```

## 配置环境变量

```bash
export OPENAI_API_KEY="your-openai-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # 可选，自定义地址
export BING_SEARCH_KEY="your-bing-search-key"  # 图片搜索需要
```

## 运行测试

```bash
# 模块导入测试
python -c "from src.core.template_parser import TemplateParser; print('OK')"

# 启动服务
cd src/api
uvicorn main:app --reload --port 8000

# 访问文档
open http://localhost:8000/docs
```

## 测试流程

1. **上传模板** → 调用 `/api/parse-template` 解析
2. **上传资料** → 调用 `/api/organize-content` 整理内容
3. **确认后生成** → 调用 `/api/generate-ppt` 下载结果

## 已知限制（MVP 版本）

- python-pptx 对非常复杂的母版和样式支持有限
- 图表生成功能还需要进一步完善
- 完整的表格生成需要更多代码
