# 打包为 Windows 可执行程序

## 方法一：在 Windows 本地打包（推荐，最简单）

### 前置准备

1. 安装 Python 3.8+ for Windows
2. 克隆或解压项目代码
3. 打开命令提示符，进入项目目录

### 步骤

```cmd
:: 1. 安装依赖
pip install -r requirements.txt
pip install pyinstaller

:: 2. 使用 spec 文件打包
pyinstaller build-windows.spec

:: 3. 等待打包完成，输出在 dist/ 文件夹
:: 生成 dist/ai-ppt-generator.exe
```

### 运行

打包完成后，在 `dist/` 目录找到 `ai-ppt-generator.exe`，运行前需要设置环境变量：

```cmd
set OPENAI_API_KEY=your-api-key-here
set BING_SEARCH_KEY=your-bing-key-here  :: 可选
ai-ppt-generator.exe
```

然后浏览器访问 `http://localhost:8000/docs` 即可使用。

---

## 方法二：在 WSL 或 Linux 交叉编译（不推荐）

如果你使用 WSL2，可以在 WSL 中安装 mingw-w64 交叉编译工具链，然后用 PyInstaller 打包。但这条路比较坑，不推荐。

还是方法一简单直接。

---

## ⚠️ 注意事项

1. **打包大小**：PyInstaller 打包后大约 50-80MB，因为包含了 Python 运行环境
2. **首次启动**：exe 首次启动会慢一点，正常现象
3. **杀毒软件**：部分杀毒可能误报，可以添加信任
4. **API Key 安全**：程序需要你的 OpenAI API Key，key 只在本地使用，不会上传

---

## 📦 输出结果

| 文件 | 位置 | 说明 |
|------|------|------|
| `ai-ppt-generator.exe` | `dist/` | 可执行程序 |
| 依赖 | 内置 | 不需要用户再安装 Python |

---

## 🚀 启动后

启动后和 Linux 版使用方法完全一样，打开浏览器访问 `http://localhost:8000/docs` 就能看到 API 文档，开始使用了。
