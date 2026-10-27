# 🍉 FruitRecognizer · 水果识别桌面应用

> 调用电脑摄像头，一键识别画面中的水果；非水果时自动给出提示。
> 基于 PyQt6 原生窗口 + 智谱 GLM-4V 视觉大模型，DWM 真毛玻璃、Win11 圆角、回弹动效。

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Qt](https://img.shields.io/badge/PyQt6-6.5+-green.svg)](https://www.riverbankcomputing.com/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6.svg)](https://www.microsoft.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ 特性

- 📷 **实时摄像头画面**：OpenCV 直读本机摄像头，圆角画框
- 🍎 **一键识别**：点「识别画面」截取当前帧，送视觉大模型识别
- 🔍 **覆盖任意常见水果**：不训练本地分类模型，改用通用视觉大模型，任意角度、任意品种都能认
- ⚠️ **非水果提示**：画面主体不是水果时自动切红色警示卡片
- 🪟 **DWM 毛玻璃**：Windows 真亚克力模糊背景，可透出桌面
- 🌗 **深浅色切换**：右上角一键切换，主题色随窗口
- 🎬 **动效**：识别中绿色扫描线、结果卡片回弹入场、窗口淡入
- 🧩 **模块化**：核心识别逻辑（`core/`）与 UI（`app/`）完全分离

## 📁 项目结构

```
fruit-recognizer/
├── core/                  # ① 模型源文件：纯识别逻辑，无 UI
│   ├── __init__.py
│   └── recognizer.py      #   recognize_frame() 核心函数
├── app/                   # ② 带 UI 的完整桌面应用
│   ├── __init__.py
│   └── fruit_app.py       #   PyQt6 主窗口、摄像头、结果卡片
├── docs/
│   └── usage.md           # 使用文档
├── screenshots/           # 界面截图
├── requirements.txt
├── LICENSE                # MIT
└── README.md
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置智谱 API Key

在 [智谱开放平台](https://open.bigmodel.cn/) 申请 API Key，然后任选一种方式配置：

```bash
# 方式一：环境变量
set FRUIT_API_KEY=你的Key

# 方式二：直接编辑 app/fruit_app.py 顶部的 API_KEY 变量
```

### 3. 运行桌面应用

```bash
python app/fruit_app.py
```

### 4. （可选）打包为单文件 EXE

```bash
pyinstaller --noconfirm --windowed -F --name fruit-recognizer app/fruit_app.py
```

## 🧠 作为库使用（仅核心识别模块）

```python
import cv2
from core.recognizer import recognize_frame

frame = cv2.imread("apple.jpg")   # BGR numpy 数组
result = recognize_frame(frame, api_key="你的Key")
print(result["name"], result["emoji"])   # 苹果 🍎
print(result["desc"])                    # 脆甜多汁，一天一个
print(result["is_fruit"])                # True / False
```

## 📸 界面截图

见 [`screenshots/`](screenshots/) 目录。

- 深色主题 · 实时摄像头画面
- 识别结果卡片（水果 · 非水果两种状态）
- 浅色主题 · 毛玻璃效果

## 🧪 技术说明

| 模块 | 选型 | 说明 |
|---|---|---|
| 摄像头 | OpenCV (`cv2`) | Windows 下用 DSHOW 后端，兼容性最好 |
| 窗口 | PyQt6 | 原生无边框 + DWM Acrylic，非网页套壳 |
| 识别 | 智谱 GLM-4V-Flash | 通用视觉大模型，base64 JPEG 上传 |
| 毛玻璃 | `SetWindowCompositionAttribute` | Win10/11 真亚克力模糊 |
| 圆角 | `DwmSetWindowAttribute(33)` | Win11 窗口圆角 |

## 📋 已知限制

- 识别需要联网（调用智谱视觉接口）
- 打包后单文件约 100MB（内含 OpenCV 运行库）
- 首次启动单文件 EXE 会自解压数秒
- 个别 emoji 在某些系统字体下可能显示为黑白

## 📄 License

[MIT](LICENSE) © 深深
